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
# Action required: mentor to review and decide canonical key names / sources
# =============================================================================
# GAP | Template location         | Literal key used        | Notes
# ─────────────────────────────────────────────────────────────────────────────
# 1   | Table 2.1                 | 'latitude'              | injected from weather_data
# 2   | Table 2.1                 | 'longitude'             | injected from weather_data
# 3   | Table 2.1                 | 'seismic_zone'          | injected from weather_data
# 4   | Table 2.1                 | 'wind_speed'            | injected from weather_data
# 5   | Table 2.1                 | 'shade_temp_max'        | injected from weather_data
# 6   | Table 2.1                 | 'shade_temp_min'        | injected from weather_data
# 7   | Table 2.2 / Exec Summary  | 'num_lanes'             | computed via IRC6 table_6()
# 8   | Table 2.2                 | 'overall_bridge_width'  | computed by sizing engine
# 9   | Exec Summary (Proj Ovw)   | 'overall_design_status' | runtime-injected by backend
# 10  | Exec Summary (Proj Ovw)   | 'governing_check'       | runtime-injected by backend
# 11  | Exec Summary (Proj Ovw)   | 'max_ur'                | runtime-injected by backend
# 12  | Exec Summary (Table 1)    | 'section_designation'   | runtime-injected by backend
# 13  | Table 2.5                 | 'crash_barrier_type'    | KEY_CRASH_BARRIER_TYPE is a list
# 14  | Table 2.5                 | 'median_type'           | KEY_MEDIAN_TYPE is a list
# 15  | Table 2.5                 | 'railing_type'          | KEY_RAILING_TYPE is a list
# =============================================================================

import os, shutil, logging, datetime, tempfile, subprocess
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Literal

from osdagbridge.core.utils.common import (
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
    KEY_GIRDER_SPACING,
    KEY_NO_OF_GIRDERS,
    KEY_DECK_THICKNESS,
    KEY_FOOTPATH_WIDTH,
    KEY_WEARING_COAT_MATERIAL,
    KEY_WEARING_COAT_THICKNESS,
    KEY_CRASH_BARRIER_LOAD,
    KEY_RAILING_LOAD,
    KEY_DECK_OVERHANG,
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
        return r'\placeholder{---}'
    s = s.replace('\\', r'\textbackslash{}')
    for ch, esc in [('&', r'\&'), ('%', r'\%'), ('$', r'\$'), ('#', r'\#'),
                    ('_', r'\_'), ('~', r'\textasciitilde{}'), ('^', r'\^{}'),
                    ('{', r'\{'), ('}', r'\}')]:
        s = s.replace(ch, esc)
    return s


def _v(inp, key, suffix='', default=''):
    """Safely fetch an input value with optional unit suffix."""
    val = inp.get(key, '')
    if val in ('', None):
        return default
    return f"{val}{suffix}"


def _ph(key):
    """Return a \\placeholder{key} command."""
    # Temporarily remove any existing escapes to avoid double escaping, then escape all
    escaped_key = key.replace(r'\_', '_').replace('_', r'\_')
    return r'\placeholder{' + escaped_key + '}'


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
\usepackage{titlesec}
\usepackage{titletoc}
\usepackage{lastpage}
\usepackage{makecell}

\definecolor{osdagGreen}{HTML}{91B014}

\fancypagestyle{main}{
  \fancyhf{}
  \fancyhead[L]{""" + pn + r""" $|$ """ + jn + r"""}
  \fancyhead[R]{""" + rd + r""" $|$ """ + rv + r"""}
  \fancyfoot[L]{Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay}
  \fancyfoot[R]{Page \thepage\ of \pageref{LastPage}}
  \renewcommand{\headrule}{\color{osdagGreen}\hrule width\headwidth height 1pt \vspace{2pt}}
  \renewcommand{\footrule}{\vspace{-8pt}\color{osdagGreen}\hrule width\headwidth height 1pt \vspace{6pt}}
}
\fancypagestyle{plain}{
  \fancyhf{}
  \fancyhead[L]{""" + pn + r""" $|$ """ + jn + r"""}
  \fancyhead[R]{""" + rd + r""" $|$ """ + rv + r"""}
  \fancyfoot[L]{Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay}
  \fancyfoot[R]{Page \thepage\ of \pageref{LastPage}}
  \renewcommand{\headrule}{\color{osdagGreen}\hrule width\headwidth height 1pt \vspace{2pt}}
  \renewcommand{\footrule}{\vspace{-8pt}\color{osdagGreen}\hrule width\headwidth height 1pt \vspace{6pt}}
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
        rhs = r'\textit{(Org Logo)}'

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
\textbf{Report Version} & """ + (_tex(m.subtitle) if m.subtitle else r"Rev 0 --- For Review") + r""" \\
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

def executive_summary(inp, fig_paths) -> str:
    plan_fig = _fig_or_placeholder(fig_paths.get('plan'), 'Figure 1 -- Overall Bridge Plan')
    cs_fig = _fig_or_placeholder(fig_paths.get('cross_section'),
                                  'Figure 2 -- Typical Cross-Section (with girder, deck, barriers, footpath)')
    geom_fig = _fig_or_placeholder(fig_paths.get('final_geometry'),
                                    'Figure 3 -- 3D View of Bridge Superstructure')

    # All girders share the same section, governing check, and UR (from input_dict)
    sec = _tex(str(inp.get('section_designation', ''))) or _ph('Section')  # GAP: not in common.py (runtime-injected)
    gov = _tex(str(inp.get('governing_check', ''))) or _ph('Check')
    ur  = _tex(str(inp.get('max_ur', ''))) or _ph('UR')

    sections = f"Section Designation & {sec} & {sec} & {sec} & {sec} & {sec} & {sec} \\\\"
    gov_checks = f"Governing Check & {gov} & {gov} & {gov} & {gov} & {gov} & {gov} \\\\"
    urs = f"Utilization Ratio & {ur} & {ur} & {ur} & {ur} & {ur} & {ur} \\\\"

    return r"""
\newpage
{\centering\Large\bfseries Executive Summary\par}
\addcontentsline{toc}{chapter}{Executive Summary}
\vspace{0.8em}

This section provides a concise summary of the bridge design, key inputs, governing loads, and final design outcomes.

\section*{Project Overview}
\addcontentsline{toc}{section}{Project Overview}
\label{sec:project-overview}

\begin{table}[H]
\begin{tabular}{|L{5.5cm}|L{8.5cm}|}
\hline
\textbf{Bridge Type} & Steel I-Girder Bridge \\
\hline
\textbf{Design Standard} & IRC 5, IRC 6, IRC 22, IRC 24, IS 800 \\
\hline
\textbf{Span} & """ + (_v(inp, KEY_SPAN, ' m') or _ph('Span Length')) + r""" \\
\hline
\textbf{Carriageway Width} & """ + (_v(inp, KEY_CARRIAGEWAY_WIDTH, ' m') or _ph('Carriageway Width')) + r""" \\
\hline
\textbf{No. of Traffic Lanes} & """ + (_v(inp, 'num_lanes') or _ph('No. of Lanes')) + r""" \\
\hline
\textbf{No. of Girders} & """ + (_v(inp, KEY_NO_OF_GIRDERS) or _ph('No. of Girders')) + r""" \\
\hline
\textbf{Girder Spacing} & """ + (_v(inp, KEY_GIRDER_SPACING) or _ph('Girder Spacing')) + r""" \\
\hline
\textbf{Deck Thickness} & """ + (_v(inp, KEY_DECK_THICKNESS) or _ph('Deck Thickness')) + r""" \\
\hline
\textbf{Overall Design Status} & """ + (_v(inp, 'overall_design_status') or _ph('PASS / FAIL')) + r""" \\
\hline
\textbf{Governing Check} & """ + (_v(inp, 'governing_check') or _ph('e.g. Deflection --- L/600')) + r""" \\
\hline
\textbf{Overall Utilization Ratio (max)} & """ + (_v(inp, 'max_ur') or _ph('Value')) + r""" \\
\hline
\end{tabular}
\end{table}

""" + plan_fig + r"""

\newpage

""" + cs_fig + '\n\n' + geom_fig + r"""

\noindent\textbf{Table 1 -- Final Bridge Geometry (after optimization)}

\vspace{0.4em}
\noindent
\begin{tabular}{|C{2.8cm}|C{1.8cm}|C{1.8cm}|C{1.8cm}|C{1.8cm}|C{1.8cm}|C{1.8cm}|}
\hline
  \textbf{} &
  \textbf{Girder 1} &
  \textbf{Girder 2} &
  \textbf{Girder 3} &
  \textbf{Girder 4} &
  \multicolumn{2}{c|}{\textbf{Girder 5}} \\
\hline
Member ID & G1M1 & G2M1 & G3M1 & G4M1 & G5M1 & G5M2 \\
\hline
""" + sections + r"""
\hline
""" + gov_checks + r"""
\hline
""" + urs + r"""
\hline
\end{tabular}

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

\begin{table}[H]
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
\end{table}

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


def ch2_input_parameters(m, inp):
    return r"""
\chapter{Input Parameters}

\setlength{\abovecaptionskip}{2pt}
\setlength{\belowcaptionskip}{2pt}

This section documents all inputs provided to OsdagBridge. User-provided inputs are clearly distinguished from software-assumed defaults. Where the user did not supply a value, the software has applied the IRC/IS code default or an empirical guideline; these are annotated [SOFTWARE DEFAULT].

\section{Basic Inputs (User-Defined)}
\label{sec:basic-inputs}

\noindent\textit{Note: These inputs are mandatory and were provided by the user.}

\noindent\textbf{Table 2.1 Project Location}
\label{subsec:project-location}

\begin{table}[H]
\vspace{-6pt}
\begin{tabular}{|L{5.5cm}|L{8.5cm}|}
\hline
\textbf{Project Location} & """ + _tex(m.project_location) + r""" \\
\hline
\textbf{Latitude / Longitude} & """ + (_v(inp,'latitude') or _ph('lat')) + ', ' + (_v(inp,'longitude') or _ph('lon')) + r""" \\
\hline
\textbf{Seismic Zone (IRC 6)} & """ + (_v(inp,'seismic_zone') or _ph('Zone II / III / IV / V')) + r""" \\
\hline
\textbf{Basic Wind Speed (IRC 6)} & """ + (_v(inp,'wind_speed',' m/s') or _ph('Vb') + ' m/s') + r""" \\
\hline
\textbf{Shade Temp. Max / Min (IRC 6)} & """ + (_v(inp,'shade_temp_max','') or _ph('Max')) + r""" °C / """ + (_v(inp,'shade_temp_min','') or _ph('Min')) + r""" °C \\
\hline
\end{tabular}
\end{table}

\noindent\textbf{Table 2.2 Bridge Geometry}
\label{subsec:bridge-geometry}

\begin{table}[H]
\vspace{-6pt}
\begin{tabular}{|L{5.5cm}|L{8.5cm}|}
\hline
\textbf{Type of Structure} & Highway Bridge \\
\hline
\textbf{Span (m)} & """ + (_v(inp, KEY_SPAN,' m') or _ph('L') + ' m') + r""" \\
\hline
\textbf{Carriageway Width (m)} & """ + (_v(inp, KEY_CARRIAGEWAY_WIDTH,' m') or _ph('CW') + ' m') + r""" \\
\hline
\textbf{Include Median} & """ + (_v(inp, KEY_INCLUDE_MEDIAN) or 'Yes / No') + r""" \\
\hline
\textbf{Footpath} & """ + (_v(inp, KEY_FOOTPATH) or 'None / Single / Both') + r""" \\
\hline
\textbf{Skew Angle (degrees)} & """ + (_v(inp, KEY_SKEW_ANGLE,'°') or _ph('Angle') + '°') + r""" (IRC 24 Cl. 504.8 limit: $\pm$15°) \\
\hline
\end{tabular}
\end{table}

\noindent\textbf{Table 2.3 Material Selection}
\label{subsec:material}

\begin{table}[H]
\vspace{-6pt}
\begin{tabular}{|L{5.5cm}|L{8.5cm}|}
\hline
\textbf{Girder Steel Grade (IS 2062)} & """ + (_v(inp, KEY_GIRDER) or _ph('e.g. E 350')) + r""" \\
\hline
\textbf{Cross Bracing Steel Grade} & """ + (_v(inp, KEY_CROSS_BRACING) or _ph('e.g. E 350')) + r""" \\
\hline
\textbf{End Diaphragm Steel Grade} & """ + (_v(inp, KEY_END_DIAPHRAGM) or _ph('e.g. E 350')) + r""" \\
\hline
\textbf{Concrete Deck Grade (IRC 22)} & """ + (_v(inp, KEY_DECK_CONCRETE_GRADE_BASIC) or _ph('e.g. M 40')) + r""" \\
\hline
\end{tabular}
\end{table}

\newpage
\section{Additional Inputs}
\label{sec:additional-inputs}

Where the user has modified additional inputs, those values are reported here. Where no modification was made, the software default is shown.

\noindent\textbf{Table 2.4  Typical Section Details}

\begin{table}[H]
\vspace{-6pt}
\begin{tabularx}{\textwidth}{|L{5.5cm}|X|}
\hline
\textbf{Overall Bridge Width (m)} & """ + (_v(inp,'overall_bridge_width') or _ph('Calculated')) + r""" \\[6pt]
\hline
\textbf{No. of Girders} & """ + (_v(inp, KEY_NO_OF_GIRDERS) or _ph('n')) + r""" [SOFTWARE DEFAULT / USER] \\[6pt]
\hline
\textbf{Girder Spacing (m)} & """ + (_v(inp, KEY_GIRDER_SPACING,' m') or _ph('s') + ' m') + r""" [SOFTWARE DEFAULT: 2.5 m] \\[6pt]
\hline
\textbf{Deck Overhang Width (m)} & """ + (_v(inp, KEY_DECK_OVERHANG,' m') or _ph(r'd\_oh') + ' m') + r""" [SOFTWARE DEFAULT: 0.35 x spacing] \\[6pt]
\hline
\textbf{Deck Thickness (mm)} & """ + (_v(inp, KEY_DECK_THICKNESS,' mm') or _ph('dt') + ' mm') + r""" [SOFTWARE DEFAULT: 200 mm] \\[6pt]
\hline
\textbf{Footpath Width (m)} & """ + (_v(inp, KEY_FOOTPATH_WIDTH,' m') or _ph('$f_w$') + ' m') + r""" (IRC 5 Cl. 104.3.6 min: 1.5 m) \\[6pt]
\hline
\textbf{No. of Traffic Lanes} & """ + (_v(inp,'num_lanes') or _ph(r'n\_lanes')) + r""" (per IRC 5 Cl. 104.3.1) \\[6pt]
\hline
\end{tabularx}
\end{table}

\vspace{0.8em}
\noindent\textbf{Table 2.5  Components Details}

\begin{table}[H]
\vspace{-6pt}
\begin{tabularx}{\textwidth}{|L{5.5cm}|X|}
\hline
\textbf{Crash Barrier Type} & """ + (_v(inp,'crash_barrier_type') or _ph('IRC 5 RCC / Metallic / Custom')) + r""" \\[6pt]
\hline
\textbf{Crash Barrier Load (kN/m)} & """ + (_v(inp, KEY_CRASH_BARRIER_LOAD) or _ph('Load')) + r""" \\[6pt]
\hline
\textbf{Median Type} & """ + (_v(inp,'median_type') or _ph('IRC 5 Raised Kerb / N/A')) + r""" \\[6pt]
\hline
\textbf{Railing Type} & """ + (_v(inp,'railing_type') or _ph('IRC 5 RCC / Steel / N/A')) + r""" \\[6pt]
\hline
\textbf{Railing Load (kN/m)} & 1.5 kN/m [SOFTWARE DEFAULT per IRC 6 Cl. 206.5] \\[6pt]
\hline
\textbf{Wearing Course Material} & """ + (_v(inp, KEY_WEARING_COAT_MATERIAL) or _ph('Bituminous / Concrete')) + r""" \\[6pt]
\hline
\textbf{Wearing Course Thickness (mm)} & """ + (_v(inp, KEY_WEARING_COAT_THICKNESS,' mm') or _ph(r'wc\_t') + ' mm') + r""" [SOFTWARE DEFAULT: 80 mm] \\[6pt]
\hline
\end{tabularx}
\end{table}

""" + _girder_tables() + r"""

""" + _bracing_tables() + r"""

""" + _shear_connector_table(inp) + r"""

""" + _safety_factors_table(inp)


def _girder_tables():
    return r"""
\newpage
\noindent\textbf{Table 2.6  Member Properties: Girder Details}

\vspace{0.4em}
\noindent
\begin{table}[H]
\captionsetup{justification=raggedright,singlelinecheck=false}
\caption*{\textbf{Table 2.6(a)  Girder General Information}}
\vspace{4pt}
\begin{tabularx}{\textwidth}{|L{2.2cm}|L{1.8cm}|X|X|X|}
\hline
\textbf{Girder} & \textbf{Member ID} & \textbf{Design Mode} & \textbf{Girder Type} & \textbf{Girder Symmetry} \\[6pt]
\hline
Girder 1 & G1M1 & Optimized / Customized & Welded Plate Girder / Rolled & Symmetric / Unsymmetric \\[8pt]
\hline
Girder 2 & G2M1 & Optimized / Customized & Welded Plate Girder / Rolled & Symmetric / Unsymmetric \\[8pt]
\hline
Girder 3 & G3M1 & Optimized / Customized & Welded Plate Girder / Rolled & Symmetric / Unsymmetric \\[8pt]
\hline
Girder 4 & G4M1 & Optimized / Customized & Welded Plate Girder / Rolled & Symmetric / Unsymmetric \\[8pt]
\hline
Girder 5A & G5M1 & Optimized / Customized & Welded Plate Girder / Rolled & Symmetric / Unsymmetric \\[8pt]
\hline
Girder 5B & G5M2 & Optimized / Customized & Welded Plate Girder / Rolled & Symmetric / Unsymmetric \\[8pt]
\hline
\end{tabularx}
\end{table}

\vspace{0.6em}
\begin{table}[H]
\captionsetup{justification=raggedright,singlelinecheck=false}
\caption*{\textbf{Table 2.6(b)  Girder Section Dimensions}}
\vspace{4pt}
\begin{tabularx}{\textwidth}{|L{1.8cm}|L{2.3cm}|L{1.8cm}|X|X|}
\hline
\textbf{Girder} & \textbf{Total Depth, D (mm)} & \textbf{Web, tw (mm)} & \textbf{Top Flange (b\textsubscript{tf}, t\textsubscript{tf}) mm} & \textbf{Bottom Flange (b\textsubscript{bf}, t\textsubscript{bf}) mm} \\[6pt]
\hline
Girder 1 & \placeholder{D} & \placeholder{tw} & \placeholder{btf}, \placeholder{ttf} & \placeholder{bbf}, \placeholder{tbf} \\[8pt]
\hline
Girder 2 & \placeholder{D} & \placeholder{tw} & \placeholder{btf}, \placeholder{ttf} & \placeholder{bbf}, \placeholder{tbf} \\[8pt]
\hline
Girder 3 & \placeholder{D} & \placeholder{tw} & \placeholder{btf}, \placeholder{ttf} & \placeholder{bbf}, \placeholder{tbf} \\[8pt]
\hline
Girder 4 & \placeholder{D} & \placeholder{tw} & \placeholder{btf}, \placeholder{ttf} & \placeholder{bbf}, \placeholder{tbf} \\[8pt]
\hline
Girder 5A & \placeholder{D} & \placeholder{tw} & \placeholder{btf}, \placeholder{ttf} & \placeholder{bbf}, \placeholder{tbf} \\[8pt]
\hline
Girder 5B & \placeholder{D} & \placeholder{tw} & \placeholder{btf}, \placeholder{ttf} & \placeholder{bbf}, \placeholder{tbf} \\[8pt]
\hline
\end{tabularx}
\end{table}

\vspace{0.6em}
\begin{table}[H]
\captionsetup{justification=raggedright,singlelinecheck=false}
\caption*{\textbf{Table 2.6(c)  Girder Restraint and Stiffener Details}}
\vspace{4pt}
\begin{tabularx}{\textwidth}{|L{1.8cm}|X|X|X|X|}
\hline
\textbf{Girder} & \textbf{Torsional / Warping Restraint} & \textbf{Web Philosophy} & \textbf{Intermediate Stiffeners} & \textbf{Longitudinal / End Panel Stiffeners} \\[6pt]
\hline
Girder 1 & \placeholder{Fully / Partially}, \placeholder{Both Flange / No Restraint} & Simple Post Critical / Tension Field & Yes / No; Spacing: \placeholder{c} mm; Thickness: \placeholder{ts} mm & Longitudinal: Yes / No / N.R.; End Panel: Yes; \placeholder{$t_{s,end}$} mm \\[8pt]
\hline
Girder 2 & \placeholder{Fully / Partially}, \placeholder{Both Flange / No Restraint} & Simple Post Critical / Tension Field & Yes / No; Spacing: \placeholder{c} mm; Thickness: \placeholder{ts} mm & Longitudinal: Yes / No / N.R.; End Panel: Yes; \placeholder{$t_{s,end}$} mm \\[8pt]
\hline
Girder 3 & \placeholder{Fully / Partially}, \placeholder{Both Flange / No Restraint} & Simple Post Critical / Tension Field & Yes / No; Spacing: \placeholder{c} mm; Thickness: \placeholder{ts} mm & Longitudinal: Yes / No / N.R.; End Panel: Yes; \placeholder{$t_{s,end}$} mm \\[8pt]
\hline
Girder 4 & \placeholder{Fully / Partially}, \placeholder{Both Flange / No Restraint} & Simple Post Critical / Tension Field & Yes / No; Spacing: \placeholder{c} mm; Thickness: \placeholder{ts} mm & Longitudinal: Yes / No / N.R.; End Panel: Yes; \placeholder{$t_{s,end}$} mm \\[8pt]
\hline
Girder 5A & \placeholder{Fully / Partially}, \placeholder{Both Flange / No Restraint} & Simple Post Critical / Tension Field & Yes / No; Spacing: \placeholder{c} mm; Thickness: \placeholder{ts} mm & Longitudinal: Yes / No / N.R.; End Panel: Yes; \placeholder{$t_{s,end}$} mm \\[8pt]
\hline
Girder 5B & \placeholder{Fully / Partially}, \placeholder{Both Flange / No Restraint} & Simple Post Critical / Tension Field & Yes / No; Spacing: \placeholder{c} mm; Thickness: \placeholder{ts} mm & Longitudinal: Yes / No / N.R.; End Panel: Yes; \placeholder{$t_{s,end}$} mm \\[8pt]
\hline
\end{tabularx}
\end{table}
"""


def _bracing_tables():
    return r"""
\newpage
\noindent\textbf{Table 2.7  Member Properties: Cross Bracing Details}

\vspace{0.4em}
\noindent
\setlength{\tabcolsep}{4pt}
\begin{longtable}{|L{2.2cm}|L{2.2cm}|L{3.0cm}|L{2.5cm}|C{1.8cm}|C{1.8cm}|}
\hline
\textbf{Location} & \textbf{Member IDs} & \textbf{Type of Bracing} & \textbf{Bracing Section} & \textbf{Spacing (m)} & \textbf{No. of Panels} \\
\hline
Between Girders 1 and 2 & B1M1 -- B1M10 & K-Bracing / X-Bracing [SOFTWARE DEFAULT] & \placeholder{e.g. ISA 100x100x8} & \placeholder{$s_{br}$} & \placeholder{$n_{br}$} \\[6pt]
\hline
Between Girders 2 and 3 & B2M1 -- B2M10 & K-Bracing / X-Bracing [SOFTWARE DEFAULT] & \placeholder{e.g. ISA 100x100x8} & \placeholder{$s_{br}$} & \placeholder{$n_{br}$} \\[6pt]
\hline
Between Girders 3 and 4 & B3M1 -- B3M10 & K-Bracing / X-Bracing [SOFTWARE DEFAULT] & \placeholder{e.g. ISA 100x100x8} & \placeholder{$s_{br}$} & \placeholder{$n_{br}$} \\[6pt]
\hline
Between Girders 4 and 5 & B4M1 -- B4M10 & K-Bracing / X-Bracing [SOFTWARE DEFAULT] & \placeholder{e.g. ISA 100x100x8} & \placeholder{$s_{br}$} & \placeholder{$n_{br}$} \\[6pt]
\hline
\end{longtable}

\noindent\textbf{Table 2.8  Member Properties: End Diaphragm Details}

\vspace{0.4em}
\noindent
\setlength{\tabcolsep}{4pt}
\begin{longtable}{|L{2.2cm}|L{2.2cm}|L{3.0cm}|L{2.5cm}|C{1.8cm}|C{1.8cm}|}
\hline
\textbf{Location} & \textbf{Member IDs} & \textbf{Type of Bracing} & \textbf{Bracing Section} & \textbf{Spacing (m)} & \textbf{No. of Panels} \\
\hline
Between Girders 1 and 2 & E1M1, E1M2 & K-Bracing / X-Bracing [SOFTWARE DEFAULT] & \placeholder{e.g. ISA 100x100x8} & \placeholder{$s_{br}$} & \placeholder{$n_{br}$} \\[6pt]
\hline
Between Girders 2 and 3 & E2M1, E2M2 & K-Bracing / X-Bracing [SOFTWARE DEFAULT] & \placeholder{e.g. ISA 100x100x8} & \placeholder{$s_{br}$} & \placeholder{$n_{br}$} \\[6pt]
\hline
Between Girders 3 and 4 & E3M1, E3M2 & K-Bracing / X-Bracing [SOFTWARE DEFAULT] & \placeholder{e.g. ISA 100x100x8} & \placeholder{$s_{br}$} & \placeholder{$n_{br}$} \\[6pt]
\hline
Between Girders 4 and 5 & E4M1, E4M2 & K-Bracing / X-Bracing [SOFTWARE DEFAULT] & \placeholder{e.g. ISA 100x100x8} & \placeholder{$s_{br}$} & \placeholder{$n_{br}$} \\[6pt]
\hline
\end{longtable}
"""


def _shear_connector_table(inp):
    return r"""
\label{subsec:shear-connectors}

\vspace{2.2em}
\noindent\textbf{Table 2.9  Shear Connector Details}

\vspace{0.4em}
\begin{tabularx}{\textwidth}{|L{5.5cm}|X|}
\hline
\textbf{Stud Diameter (mm)} & """ + (_v(inp,'stud_diameter',' mm') or _ph('$d_{stud}$') + ' mm') + r""" [SOFTWARE DEFAULT: 22 mm] \\[6pt]
\hline
\textbf{Stud Height (mm)} & """ + (_v(inp,'stud_height',' mm') or _ph('$h_{stud}$') + ' mm') + r""" [SOFTWARE DEFAULT: 100 mm] \\[6pt]
\hline
\textbf{Stud fy (MPa)} & """ + (_v(inp,'stud_fy',' MPa') or _ph('$f_{ys}$') + ' MPa') + r""" [SOFTWARE DEFAULT: 385 MPa] \\[6pt]
\hline
\textbf{Stud fu (MPa)} & """ + (_v(inp,'stud_fu',' MPa') or _ph('$f_{us}$') + ' MPa') + r""" [SOFTWARE DEFAULT: 495 MPa] \\[6pt]
\hline
\textbf{No. of Studs per Section} & """ + (_v(inp,'num_studs') or _ph('$n_s$')) + r""" [SOFTWARE DEFAULT: 2] \\[6pt]
\hline
\end{tabularx}
"""


def _safety_factors_table(inp):
    return r"""
\label{subsec:safety-factors}

\vspace{2.2em}
\noindent\textbf{Table 2.10  Partial Safety Factors}

\vspace{0.3em}
\noindent\textit{Note: All values are per IRC 22 Table 1 unless user-modified.}

\vspace{0.4em}
\begin{tabularx}{\textwidth}{|L{5.5cm}|X|}
\hline
\textbf{$\gamma_{M0}$ (Yielding / Buckling)} & """ + str(inp.get('gamma_m0', '1.10')) + r""" \\[6pt]
\hline
\textbf{$\gamma_{M1}$ (Ultimate Stress)} & """ + str(inp.get('gamma_m1', '1.25')) + r""" \\[6pt]
\hline
\textbf{$\gamma_C$ (Concrete, Basic)} & """ + str(inp.get('gamma_c', '1.50')) + r""" \\[6pt]
\hline
\textbf{$\gamma_s$ (Reinforcement)} & """ + str(inp.get('gamma_s', '1.15')) + r""" \\[6pt]
\hline
\textbf{$\gamma_v$ (Shear Connectors)} & """ + str(inp.get('gamma_v', '1.25')) + r""" \\[6pt]
\hline
\textbf{$\gamma_{fft}$ (Fatigue Load)} & """ + str(inp.get('gamma_fft', '1.00')) + r""" \\[6pt]
\hline
\textbf{$\gamma_{Mft}$ (Fatigue Strength)} & """ + str(inp.get('gamma_mft', '1.35')) + r""" \\[6pt]
\hline
\end{tabularx}
"""


# Chapters 3-5: Loads, Analysis, Design Checks — exact LaTeX template


def ch3_loads(inp):
    return r"""
\chapter{Loads and Load Combinations}

This section summarizes all loads applied to the bridge and the load combinations considered for analysis and design.

\vspace{1em}
\noindent\textbf{Table 3.1  Dead Load -- Self Weight}

\begin{table}[H]
\vspace{-6pt}
\begin{tabularx}{\textwidth}{|L{5.5cm}|X|}
\hline
\textbf{Steel Self-Weight Applied} & Yes [per member volume x 78.5 kN/m\textsuperscript{3}] \\[6pt]
\hline
\textbf{Concrete Deck Weight} & Yes [per slab area x thickness x 25 kN/m\textsuperscript{3}] \\[6pt]
\hline
\textbf{Self-Weight Factor} & 1.0 [SOFTWARE DEFAULT] \\[6pt]
\hline
\end{tabularx}
\end{table}

\vspace{1em}
\noindent\textbf{Table 3.2  Dead Load for Surfacing (DW)}

\begin{table}[H]
\vspace{-6pt}
\begin{tabularx}{\textwidth}{|L{5.5cm}|X|}
\hline
\textbf{Wearing Course Load} & """ + (_v(inp, KEY_WEARING_COAT_MATERIAL) or _ph('Density')) + r""" x """ + (_v(inp, KEY_WEARING_COAT_THICKNESS) or _ph('Thickness')) + r""" \\[6pt]
\hline
\textbf{Additional SIDL (Crash Barrier)} & """ + (_v(inp, KEY_CRASH_BARRIER_LOAD) or _ph('Load')) + r""" kN/m per barrier \\[6pt]
\hline
\textbf{Railing Load} & 1.5 kN/m per railing [IRC 6 Cl. 206.5] \\[6pt]
\hline
\end{tabularx}
\end{table}

\vspace{1em}
\noindent\textbf{Table 3.3  Live Loads (LL)}

\begin{table}[H]
\vspace{-6pt}
\begin{tabularx}{\textwidth}{|L{5.5cm}|X|}
\hline
\textbf{Vehicles Considered} & Class A, Class 70R Wheeled/Tracked [IRC 6] \\[6pt]
\hline
\textbf{Impact Factor (IRC 6)} & """ + (_v(inp, "impact_factor") or _ph("Value")) + r""" \\[6pt]
\hline
\textbf{Braking Load (IRC 6)} & Applied --- """ + (_v(inp, "braking_load", " kN") or _ph("Value")) + r""" \\[6pt]
\hline
\textbf{Footpath Live Load (if applicable)} & """ + (_v(inp, "footpath_live_load", " kN/m\\textsuperscript{2}") or "5 kN/m\\textsuperscript{2} [SOFTWARE DEFAULT per IRC 6]") + r""" \\[6pt]
\hline
\end{tabularx}
\end{table}

\vspace{1em}
\noindent\textbf{Table 3.4  Wind Load (WL) --- per IRC 6}

\begin{table}[H]
\vspace{-6pt}
\begin{tabularx}{\textwidth}{|L{5.5cm}|X|}
\hline
\textbf{Basic Wind Speed, Vb} & """ + (_v(inp,'wind_speed',' m/s') or _ph('Vb') + ' m/s') + r""" [from Project Location] \\[6pt]
\hline
\textbf{Terrain Type} & """ + (_v(inp, "terrain_type") or "Plain Terrain [SOFTWARE DEFAULT]") + r""" \\[6pt]
\hline
\textbf{Average Exposed Height, H (m)} & """ + (_v(inp, "avg_exposed_height", " m") or "10 m [SOFTWARE DEFAULT]") + r""" \\[6pt]
\hline
\textbf{Hourly Mean Wind Speed, Vz} & """ + str(inp.get("wind_Vz", _ph("Vz"))) + r""" m/s \\[6pt]
\hline
\textbf{Hourly Wind Pressure, Pz} & """ + str(inp.get("wind_Pz", _ph("Pz"))) + r""" N/m\textsuperscript{2} \\[6pt]
\hline
\textbf{Transverse Wind Force} & """ + str(inp.get("wind_Fw_T", _ph("Fw_T"))) + r""" kN \\[6pt]
\hline
\textbf{Longitudinal Wind Force} & """ + str(inp.get("wind_Fw_L", _ph("Fw_L"))) + r""" kN \\[6pt]
\hline
\textbf{Vertical Wind Force} & """ + str(inp.get("wind_Fw_V", _ph("Fw_V"))) + r""" kN \\[6pt]
\hline
\end{tabularx}
\end{table}

\vspace{1em}
\noindent\textbf{Table 3.5  Earthquake Load (EL) --- per IRC 6}

\begin{table}[H]
\vspace{-6pt}
\begin{tabularx}{\textwidth}{|L{5.5cm}|X|}
\hline
\textbf{Seismic Zone} & """ + (_v(inp,'seismic_zone') or _ph('Zone')) + r""" [from Project Location] \\[6pt]
\hline
\textbf{Zone Factor, Z} & """ + str(inp.get("seismic_Z", _ph("Z"))) + r""" \\[6pt]
\hline
\textbf{Importance Factor, I} & """ + (_v(inp, "importance_factor") or "1.0 [SOFTWARE DEFAULT]") + r""" \\[6pt]
\hline
\textbf{Type of Soil} & """ + (_v(inp, "soil_type") or "Type I -- Rocky [SOFTWARE DEFAULT]") + r""" \\[6pt]
\hline
\textbf{Sa/g} & """ + str(inp.get("seismic_Sa_g", _ph("Sa_g"))) + r""" \\[6pt]
\hline
\textbf{Horizontal Seismic Coefficient, Ah} & """ + str(inp.get("seismic_Ah", _ph("Ah"))) + r""" \\[6pt]
\hline
\textbf{Vertical Seismic Coefficient, Av} & """ + str(inp.get("seismic_Av", _ph("Av"))) + r""" = 2/3 $\times$ Ah \\[6pt]
\hline
\textbf{Horizontal Seismic Force} & """ + str(inp.get("seismic_Feq_L", _ph("Feq_L"))) + r""" kN (longitudinal), """ + str(inp.get("seismic_Feq_T", _ph("Feq_T"))) + r""" kN (transverse) \\[6pt]
\hline
\end{tabularx}
\end{table}

\vspace{1em}
\noindent\textbf{Table 3.6  Temperature Load (EL) --- per IRC 6}

\begin{table}[H]
\vspace{-6pt}
\begin{tabularx}{\textwidth}{|L{5.5cm}|X|}
\hline
\textbf{Maximum Shade Temperature} & """ + (_v(inp,'shade_temp_max') or _ph(r'T\_max')) + r""" $^\circ$C \\[6pt]
\hline
\textbf{Minimum Shade Temperature} & """ + (_v(inp,'shade_temp_min') or _ph('$T_{min}$')) + r""" $^\circ$C \\[6pt]
\hline
\textbf{Effective Bridge Temp. Range} & """ + str(inp.get("temp_T_eff_min", _ph("T_eff_min"))) + r""" to """ + str(inp.get("temp_T_eff_max", _ph("T_eff_max"))) + r""" $^\circ$C \\[6pt]
\hline
\textbf{Temperature Rise / Fall for Design} & +""" + str(inp.get("temp_dT_rise", _ph("dT_rise"))) + r""" $^\circ$C / -""" + str(inp.get("temp_dT_fall", _ph("dT_fall"))) + r""" $^\circ$C \\[6pt]
\hline
\end{tabularx}
\end{table}

\vspace{1em}
\noindent\textbf{Table 3.7  Load Combinations}

\vspace{0.4em}
The following load combinations were evaluated per IRC 6. The governing combination for each member is identified in the design checks section.

\begin{table}[H]
\vspace{-6pt}
\begin{tabularx}{\textwidth}{|C{3.2cm}|C{3.5cm}|C{4.5cm}|>{\centering\arraybackslash}X|}
\hline
\textbf{Combination ID} & \textbf{Description} & \textbf{Load Cases} & \textbf{Governs For} \\[6pt]
\hline
LC-ULS-1 & DL + LL (Basic) & 1.35 DL + 1.5 LL & Moment, Shear \\[6pt]
\hline
LC-ULS-2 & DL + LL + WL & 1.35 DL + 1.5 LL + 0.9 WL & Wind check \\[6pt]
\hline
LC-ULS-3 & DL + LL + EL & 1.35 DL + 0.2 LL + 1.5 EL & Seismic check \\[6pt]
\hline
LC-SLS-1 & Service (DL + LL) & 1.0 DL + 1.0 LL & Deflection, Stress \\[6pt]
\hline
LC-FAT-1 & Fatigue (LL only) & Fatigue Truck & Fatigue checks \\[6pt]
\hline
(Additional combinations per IRC 6 auto-generated by software) & ... & ... & ... \\[6pt]
\hline
\end{tabularx}
\end{table}

\noindent\textit{Note: All IRC 6 load combinations are auto-generated by OsdagBridge. User-defined custom combinations, if any, are appended.}
"""


def ch4_analysis(asum, fig_paths, bridge: "ReportDataBridge", span_m: float):
    return r"""
\chapter{Analysis Results}

A grillage model was used for structural analysis. The deck is idealized as a grid of elastic beam elements --- longitudinal members represent the composite steel girders with effective slab, and transverse members represent the slab or cross frames. This section summarizes the critical output from that analysis.

\vspace{1em}
\noindent\textbf{Table 4.1  Summary of Maximum Demands}

\begin{table}[H]
\vspace{-6pt}
\begin{tabularx}{\textwidth}{|>{\centering\arraybackslash}X|>{\centering\arraybackslash}C{2.8cm}|>{\centering\arraybackslash}C{2.2cm}|>{\centering\arraybackslash}C{2.5cm}|>{\centering\arraybackslash}C{2.2cm}|>{\centering\arraybackslash}C{1.8cm}|}
\hline
\textbf{Load Case} & \textbf{Max BM (kN-m)} & \textbf{Location (m)} & \textbf{Max SF (kN)} & \textbf{Location (m)} & \textbf{Girder} \\[6pt]
\hline
DL only & """ + bridge.get_max_bm("DL only") + r""" & """ + bridge.get_bm_location("DL only") + r""" & """ + bridge.get_max_sf("DL only") + r""" & """ + bridge.get_sf_location("DL only") + r""" & \\[6pt]
\hline
DL + LL (Class A) & """ + bridge.get_max_bm("DL + LL (Class A)") + r""" & """ + bridge.get_bm_location("DL + LL (Class A)") + r""" & """ + bridge.get_max_sf("DL + LL (Class A)") + r""" & """ + bridge.get_sf_location("DL + LL (Class A)") + r""" & \\[6pt]
\hline
DL + LL (70R) & """ + bridge.get_max_bm("DL + LL (70R)") + r""" & """ + bridge.get_bm_location("DL + LL (70R)") + r""" & """ + bridge.get_max_sf("DL + LL (70R)") + r""" & """ + bridge.get_sf_location("DL + LL (70R)") + r""" & \\[6pt]
\hline
LC-ULS-1 (Governing) & """ + bridge.get_max_bm("LC-ULS-1 (Governing)") + r""" & """ + bridge.get_bm_location("LC-ULS-1 (Governing)") + r""" & """ + bridge.get_max_sf("LC-ULS-1 (Governing)") + r""" & """ + bridge.get_sf_location("LC-ULS-1 (Governing)") + r""" & \\[6pt]
\hline
LC-SLS-1 & """ + bridge.get_max_bm("LC-SLS-1") + r""" & """ + bridge.get_bm_location("LC-SLS-1") + r""" & """ + bridge.get_max_sf("LC-SLS-1") + r""" & """ + bridge.get_sf_location("LC-SLS-1") + r""" & \\[6pt]
\hline
\end{tabularx}
\end{table}

\vspace{1em}
\noindent\textbf{Table 4.2  Reactions at Supports}

\begin{table}[H]
\vspace{-6pt}
\begin{tabularx}{\textwidth}{|>{\centering\arraybackslash}X|>{\centering\arraybackslash}X|>{\centering\arraybackslash}X|}
\hline
\textbf{Load Case} & \textbf{Left Support (kN)} & \textbf{Right Support (kN)} \\[6pt]
\hline
DL only & """ + bridge.get_reaction("left", "DL only") + r""" & """ + bridge.get_reaction("right", "DL only") + r""" \\[6pt]
\hline
DL + LL (governing) & """ + bridge.get_reaction("left", "DL + LL (governing)") + r""" & """ + bridge.get_reaction("right", "DL + LL (governing)") + r""" \\[6pt]
\hline
Seismic (EL) & """ + bridge.get_reaction("left", "Seismic (EL)") + r""" & """ + bridge.get_reaction("right", "Seismic (EL)") + r""" \\[6pt]
\hline
\end{tabularx}
\end{table}

\vspace{1em}
\noindent\textbf{Table 4.3  Deflection Summary (Live Load \& Total Load)}

\begin{table}[H]
\vspace{-6pt}
\begin{tabularx}{\textwidth}{|L{7cm}|X|}
\hline
\textbf{Deflection due to Live Load, delta\_LL} & """ + bridge.get_deflection("ll") + r""" \\[6pt]
\hline
\textbf{Allowable Live Load Deflection (L/800)} & """ + bridge.get_deflection_limit("ll", span_m) + r""" \\[6pt]
\hline
\textbf{Live Load Deflection Check Status} & """ + bridge.get_deflection_status("ll", span_m) + r""" \\[6pt]
\hline
\textbf{Deflection due to Total Load, delta\_total} & """ + bridge.get_deflection("total") + r""" \\[6pt]
\hline
\textbf{Allowable Total Deflection (L/600)} & """ + bridge.get_deflection_limit("total", span_m) + r""" \\[6pt]
\hline
\textbf{Total Load Deflection Check Status} & """ + bridge.get_deflection_status("total", span_m) + r""" \\[6pt]
\hline
\end{tabularx}
\end{table}

\vspace{1em}
\noindent
\fbox{
\parbox{0.97\textwidth}{
\textit{[ PLACEHOLDER: FIGURE --- Bending Moment Envelope: Plot of max/min BM along span for governing ULS and SLS combinations. X-axis: distance from left support (m). Y-axis: Bending Moment (kN-m). ]}
}
}

\vspace{1em}
\noindent
\fbox{
\parbox{0.97\textwidth}{
\textit{[ PLACEHOLDER: FIGURE --- Shear Force Envelope: Plot of max/min SF along span. X-axis: distance from left support (m). Y-axis: Shear Force (kN). ]}
}
}

\vspace{1em}
\noindent
Figure 3 -- 3D Grillage Model with deformed shape
"""


# Chapter 5: Design Checks — exact LaTeX template match

def ch5_design_checks(checks_data, bridge: "ReportDataBridge"):
    return r"""
\chapter{Design Checks}

This section presents all structural design checks performed by OsdagBridge. For each member, the demand from the governing load combination, the code-based capacity, and the utilization ratio are tabulated. All checks reference IS 800:2007 and IRC 22:2014 unless stated otherwise.

\section{Plate Girder Design}
\label{sec:plate-girder}

\vspace{1em}
\noindent\textbf{Table 5.1  Girder Section Properties (Final Optimized / User-selected)}

\begin{table}[H]
\vspace{-6pt}
\begin{tabularx}{\textwidth}{|L{7.5cm}|X|}
\hline
\textbf{Depth, D} & \placeholder{D\_final} mm \\[6pt]
\hline
\textbf{Flange Width, bf} & \placeholder{bf} mm (= 0.3 $\times$ \placeholder{D\_final}) \\[6pt]
\hline
\textbf{Flange Thickness, tf} & \placeholder{tf} mm (= bf / 24) \\[6pt]
\hline
\textbf{Web Thickness, tw} & \placeholder{tw} mm ($\approx$ d / 200) \\[6pt]
\hline
\textbf{Gross Area of Steel Section, A (cm²)} & \placeholder{A} \\[6pt]
\hline
\textbf{Moment of Inertia, Iz (cm⁴)} & \placeholder{Iz} \\[6pt]
\hline
\textbf{Elastic Section Modulus, Zez (cm³)} & \placeholder{Zez} \\[6pt]
\hline
\textbf{Plastic Section Modulus, Zpz (cm³)} & \placeholder{Zpz} \\[6pt]
\hline
\textbf{Effective Width of Slab, b\_eff (mm)} & \placeholder{$b_{eff}$} (per IRC 22 Cl. 603.2) \\[6pt]
\hline
\textbf{Transformed Composite Iz (cm⁴)} & \placeholder{$I_{z,comp}$} (modular ratio m = Es/Ec) \\[6pt]
\hline
\textbf{Depth to Plastic Neutral Axis (mm)} & \placeholder{xu} from top of slab \\[6pt]
\hline
\end{tabularx}
\end{table}

\vspace{1em}
\noindent\textbf{Table 5.2  Girder Section Classification}

\begin{table}[H]
\vspace{-6pt}
\begin{tabularx}{\textwidth}{|C{2.5cm}|C{3cm}|C{3.5cm}|C{2.5cm}|>{\centering\arraybackslash}X|}
\hline
\textbf{} & \textbf{Element} & \textbf{Slenderness Ratio} & \textbf{Class Limit} & \textbf{Classification} \\[6pt]
\hline
\multirow{4}{*}{\centering Girder 1 - n} & Top Flange & $(b_f - t_w) / 2t_f =$ \placeholder{val} & \placeholder{limit} & Plastic / Compact / Semi-Compact \\[6pt]
\cline{2-5}
 & Bottom Flange & $(b_f - t_w) / 2t_f =$ \placeholder{val} & \placeholder{limit} & \placeholder{class} \\[6pt]
\cline{2-5}
 & Web & d / tw = \placeholder{val} & \placeholder{limit} & \placeholder{class} \\[6pt]
\cline{2-5}
 & Overall Section & --- & --- & \placeholder{governing class} \\[6pt]
\hline
\end{tabularx}
\end{table}
\noindent\textit{Note: IS 800:2007 Table 2}

\vspace{1em}
\noindent\textbf{Table 5.3  Moment Capacity Check}

\begin{table}[H]
\vspace{-6pt}
\begin{tabularx}{\textwidth}{|C{2.5cm}|C{3.5cm}|C{3.5cm}|>{\centering\arraybackslash}X|C{1.8cm}|}
\hline
\textbf{} & \textbf{Parameter} & \textbf{Formula} & \textbf{Value} & \textbf{Status} \\[6pt]
\hline
\multirow{4}{*}{\centering Girder 1 - n} & Applied Moment, $M_u$ & from LC-ULS-1 & \placeholder{$M_u$} kN-m & --- \\[6pt]
\cline{2-5}
 & Plastic Moment, Mp & Zp $\times$ fy / $\gamma_{M0}$ & \placeholder{Mp} kN-m & --- \\[6pt]
\cline{2-5}
 & Design Moment Capacity, Md & Mp / $\gamma_{M0}$ & \placeholder{$M_d$} kN-m & --- \\[6pt]
\cline{2-5}
 & Utilization Ratio, $M_u / M_d$ & --- & \placeholder{UR} & $\leq 1.0$ \\[6pt]
\hline
\end{tabularx}
\end{table}
\noindent\textit{Note: IRC 22 Cl. 603.3.1, IS 800 Cl. 8.2.1}

\vspace{1em}
\noindent\textbf{Table 5.4  Shear Capacity Check}

\begin{table}[H]
\vspace{-6pt}
\begin{tabularx}{\textwidth}{|C{2.5cm}|C{3.5cm}|C{3.5cm}|>{\centering\arraybackslash}X|C{1.8cm}|}
\hline
\textbf{} & \textbf{Parameter} & \textbf{Formula} & \textbf{Value} & \textbf{Status} \\[6pt]
\hline
\multirow{9}{*}{\centering Girder 1 - n} & Applied Shear, $V_u$ & from LC-ULS-1 & \placeholder{$V_u$} kN & --- \\[6pt]
\cline{2-5}
 & Shear Area, Av & h $\times$ tw & \placeholder{$A_v$} mm² & --- \\[6pt]
\cline{2-5}
 & Panel Aspect Ratio, c/d & --- & \placeholder{c/d} & --- \\[6pt]
\cline{2-5}
 & Shear Buckling Coefficient, kv & 5.35 + 4 / (c/d)² & \placeholder{kv} & --- \\[6pt]
\cline{2-5}
 & Web Slenderness, $\lambda_w$ & $\sqrt{f_{yw} / (\sqrt{3} \times \tau_{cr,e})}$ & \placeholder{$\lambda_w$} & --- \\[6pt]
\cline{2-5}
 & Design Shear Stress, tau\_b & per IS 800 Cl. 8.4.2.2 & \placeholder{tb} MPa & --- \\[6pt]
\cline{2-5}
 & Shear Buckling Resistance, Vcr & Av $\times$ tau\_b & \placeholder{$V_{cr}$} kN & --- \\[6pt]
\cline{2-5}
 & Web Crippling Strength, Fg & (b1+n2) $\times$ tw $\times$ fy / $\gamma_{M0}$ & \placeholder{$F_g$} kN & PASS \\[6pt]
\cline{2-5}
 & Utilization Ratio, $V_u / V_d$ & --- & \placeholder{UR} & $\leq 1.0$ \\[6pt]
\hline
\end{tabularx}
\end{table}
\noindent\textit{Note: IS 800 Cl. 8.4, IRC 22 Cl. 603.3.3.2}

\vspace{1em}
\noindent\textbf{Table 5.5  Bending-Shear Interaction Check}

\begin{table}[H]
\vspace{-6pt}
\begin{tabularx}{\textwidth}{|C{2.5cm}|C{3.5cm}|C{3.5cm}|>{\centering\arraybackslash}X|C{1.8cm}|}
\hline
\textbf{} & \textbf{Check} & \textbf{Condition} & \textbf{Value} & \textbf{Status} \\[6pt]
\hline
\multirow{3}{*}{\centering Girder 1 - n} & High Shear Condition? & V > 0.6 Vd & Yes / No & --- \\[6pt]
\cline{2-5}
 & Reduced Moment Capacity, $M_{dv}$ & $M_d - \beta(M_d - M_{fd})$ & \placeholder{$M_{dv}$} kN-m & --- \\[6pt]
\cline{2-5}
 & Interaction Check: $M_u \leq M_{dv}$ & --- & PASS / FAIL & --- \\[6pt]
\hline
\end{tabularx}
\end{table}
\noindent\textit{Note: IS 800 Cl. 9.2.2}

\vspace{1em}
\noindent\textbf{Table 5.6  Lateral Torsional Buckling Check -- Construction Stage}

\begin{table}[H]
\vspace{-6pt}
\begin{tabularx}{\textwidth}{|C{2.5cm}|C{3.5cm}|C{3.5cm}|>{\centering\arraybackslash}X|C{1.8cm}|}
\hline
\textbf{} & \textbf{Parameter} & \textbf{Formula} & \textbf{Value} & \textbf{Status} \\[6pt]
\hline
\multirow{5}{*}{\centering Girder 1 - n} & Elastic Critical Moment, Mcr & pi²EIy/LLT² $\times$ (GIt + pi²EIw/LLT²)\textasciicircum 0.5 & \placeholder{$M_{cr}$} kN-m & --- \\[6pt]
\cline{2-5}
 & Non-dim. Slenderness, $\bar{\lambda}_{LT}$ & $\sqrt{M_p / M_{cr}}$ & \placeholder{$\bar{\lambda}_{LT}$} & --- \\[6pt]
\cline{2-5}
 & LTB Reduction Factor, chi\_LT & IS 800 Cl. 8.2.2 & \placeholder{$\chi_{LT}$} & --- \\[6pt]
\cline{2-5}
 & LTB Resistance, Mb & chi\_LT $\times$ Mp / $\gamma_{M0}$ & \placeholder{$M_b$} kN-m & --- \\[6pt]
\cline{2-5}
 & $M_u \leq M_b$ & --- & PASS / FAIL & --- \\[6pt]
\hline
\end{tabularx}
\end{table}
\noindent\textit{Note: IRC 22 Cl. 603.3.3.1, IS 800 Cl. 8.2.2}


\vspace{1em}
\noindent\textbf{Table 5.7  Stiffener Design Summary}

\begin{table}[H]
\vspace{-6pt}
\begin{tabularx}{\textwidth}{|C{2.5cm}|L{6.5cm}|>{\arraybackslash}X|}
\hline
\multirow{6}{*}{\centering Girder 1 - n} & \textbf{Shear Buckling Design Method} & Simple Post Critical / Tension Field \\[6pt]
\cline{2-3}
 & \textbf{Intermediate Stiffener Thickness (mm)} & \placeholder{ts\_i} mm \\[6pt]
\cline{2-3}
 & \textbf{Intermediate Stiffener Spacing (mm)} & \placeholder{c} mm \\[6pt]
\cline{2-3}
 & \textbf{End Panel Stiffener Thickness (mm)} & \placeholder{ts\_e} mm \\[6pt]
\cline{2-3}
 & \textbf{No. of End Panel Stiffeners} & 2 (Pair) \\[6pt]
\cline{2-3}
 & \textbf{Longitudinal Stiffeners} & Not Required / Required \\[6pt]
\hline
\end{tabularx}
\end{table}

\vspace{1em}
\noindent\textbf{Table 5.8  Intermediate Stiffener Checks}

\begin{table}[H]
\vspace{-6pt}
\begin{tabularx}{\textwidth}{|C{2.5cm}|C{3.5cm}|C{3.5cm}|>{\centering\arraybackslash}X|C{1.8cm}|}
\hline
\textbf{} & \textbf{Check} & \textbf{Required} & \textbf{Provided} & \textbf{Status} \\[6pt]
\hline
\multirow{2}{*}{\centering Girder 1 - n} & Min. Moment of Inertia, Is & $\geq$ 0.75 d tw³ = \placeholder{val} mm⁴ & \placeholder{Is\_prov} mm⁴ & PASS \\[6pt]
\cline{2-5}
 & Critical Buckling Stress, tau\_cr,e & per IS 800 Cl. 8.4.2.2 & \placeholder{tau\_cr} MPa & --- \\[6pt]
\hline
\end{tabularx}
\end{table}
\noindent\textit{Note: IS 800 Cl. 8.7.1.2}

\vspace{1em}
\noindent\textbf{Table 5.9  End Panel Stiffener Checks}

\begin{table}[H]
\vspace{-6pt}
\begin{tabularx}{\textwidth}{|C{2.5cm}|C{3.5cm}|C{3.5cm}|>{\centering\arraybackslash}X|C{1.8cm}|}
\hline
\textbf{} & \textbf{Check} & \textbf{Required} & \textbf{Provided} & \textbf{Status} \\[6pt]
\hline
\multirow{3}{*}{\centering Girder 1 - n} & Vertical Anchor Force, $V_p$ & $d \times t_w \times f_y / \sqrt{3}$ & \placeholder{$V_p$} kN & --- \\[6pt]
\cline{2-5}
 & Tension Flange Reaction, $R_{tf}$ & $V_p / 2$ & \placeholder{$R_{tf}$} kN & --- \\[6pt]
\cline{2-5}
 & Tension Flange Moment, $M_{tf}$ & $V_p \times d / 10$ & \placeholder{$M_{tf}$} kN-m & --- \\[6pt]
\hline
\end{tabularx}
\end{table}
\noindent\textit{Note: IS 800 Cl. 8.4.2.2}


\vspace{1em}
\noindent\textbf{Table 5.10  Serviceability -- Deflection Checks}

\begin{table}[H]
\vspace{-6pt}
\begin{tabularx}{\textwidth}{|C{2.5cm}|C{3.5cm}|C{3.5cm}|>{\centering\arraybackslash}X|C{2.5cm}|}
\hline
\textbf{} & \textbf{Check} & \textbf{Allowable} & \textbf{Actual} & \textbf{Status} \\[6pt]
\hline
\multirow{2}{*}{\centering Girder 1 - n} & Live Load Deflection (L/800) & \placeholder{δ\_allow\_LL} mm & \placeholder{δ\_LL} mm & PASS / FAIL \\[6pt]
\cline{2-5}
 & Total Load Deflection (L/600) & \placeholder{δ\_allow\_tot} mm & \placeholder{δ\_tot} mm & PASS / FAIL \\[6pt]
\hline
\end{tabularx}
\end{table}
\noindent\textit{Note: IRC 22 Cl. 604.3.2}

\vspace{1em}
\noindent\textbf{Table 5.11  Serviceability -- Maximum Stress Limitation}

\begin{table}[H]
\vspace{-6pt}
\begin{tabularx}{\textwidth}{|C{2.5cm}|C{3.5cm}|C{3.5cm}|>{\centering\arraybackslash}X|C{2.5cm}|}
\hline
\textbf{} & \textbf{Element} & \textbf{Allowable Stress} & \textbf{Actual Stress} & \textbf{Status} \\[6pt]
\hline
\multirow{2}{*}{\centering Girder 1 - n} & Concrete (0.48 fck) & \placeholder{allow\_c} MPa & \placeholder{actual\_c} MPa & PASS / FAIL \\[6pt]
\cline{2-5}
 & Steel (0.66 fy) & \placeholder{allow\_s} MPa & \placeholder{actual\_s} MPa & PASS / FAIL \\[6pt]
\hline
\end{tabularx}
\end{table}

\vspace{1em}
\noindent\textbf{Table 5.12  Serviceability -- Fatigue Assessment}

\begin{table}[H]
\vspace{-6pt}
\begin{tabularx}{\textwidth}{|C{2.5cm}|C{3.5cm}|C{3.5cm}|>{\centering\arraybackslash}X|C{2.5cm}|}
\hline
\textbf{} & \textbf{Element} & \textbf{Detail Category} & \textbf{Allowable Stress Range (ffd)} & \textbf{Actual Stress Range ($\gamma_{fft}$ $\times$ f)} \\[6pt]
\hline
\multirow{3}{*}{\centering Girder 1 - n} & Welded Girder Web & IS 800 Table & \placeholder{ffd} MPa & \placeholder{f\_actual} MPa --- PASS \\[6pt]
\cline{2-5}
 & Welded Girder Flange & IS 800 Table & \placeholder{ffd} MPa & \placeholder{f\_actual} MPa --- PASS \\[6pt]
\cline{2-5}
 & Shear Connectors & tau\_fn = 67 MPa & \placeholder{tau\_fd} MPa & \placeholder{tau\_actual} MPa --- PASS \\[6pt]
\hline
\end{tabularx}
\end{table}
\noindent\textit{Note: IRC 22 Cl. 605. NSC = \placeholder{n\_cycles} cycles. Capacity reduction factor mu\_r applied where plate thickness > 25 mm.}

\vspace{1em}
\noindent\textbf{Table 5.13  Girder Design Summary (DCR / Utilization Ratio)}

\vspace{0.4em}
\begin{table}[H]
\vspace{-6pt}
\begin{tabularx}{\textwidth}{|C{1.6cm}|C{2.8cm}|C{1.7cm}|C{1.7cm}|C{1.7cm}|C{1.8cm}|>{\centering\arraybackslash}X|}
\hline
\textbf{Girder} & \textbf{Governing Check} & \textbf{Moment UR} & \textbf{Shear UR} & \textbf{LTB UR} & \textbf{Deflection UR} & \textbf{Status} \\[6pt]
\hline
Girder 1 & \placeholder{Check} & \placeholder{UR} & \placeholder{UR} & \placeholder{UR} & \placeholder{UR} & PASS / FAIL \\[6pt]
\hline
Girder 2 & \placeholder{Check} & \placeholder{UR} & \placeholder{UR} & \placeholder{UR} & \placeholder{UR} & PASS / FAIL \\[6pt]
\hline
Girder 3 & \placeholder{Check} & \placeholder{UR} & \placeholder{UR} & \placeholder{UR} & \placeholder{UR} & PASS / FAIL \\[6pt]
\hline
Girder 4 & \placeholder{Check} & \placeholder{UR} & \placeholder{UR} & \placeholder{UR} & \placeholder{UR} & PASS / FAIL \\[6pt]
\hline
Girder 5A & \placeholder{Check} & \placeholder{UR} & \placeholder{UR} & \placeholder{UR} & \placeholder{UR} & PASS / FAIL \\[6pt]
\hline
Girder 5B & \placeholder{Check} & \placeholder{UR} & \placeholder{UR} & \placeholder{UR} & \placeholder{UR} & PASS / FAIL \\[6pt]
\hline
\end{tabularx}
\end{table}
\noindent\textit{Note: UR = Demand / Capacity. A value $\leq 1.0$ indicates a passing check. Governing check identifies the critical design criterion for each girder.}

\vspace{1em}
\noindent\textbf{Table 5.14  Shear Connector Capacity}

\begin{table}[H]
\vspace{-6pt}
\begin{tabularx}{\textwidth}{|C{4cm}|C{5cm}|>{\centering\arraybackslash}X|C{3.5cm}|}
\hline
\textbf{Parameter} & \textbf{Formula} & \textbf{Value} & \textbf{Reference} \\[6pt]
\hline
Design Resistance, $Q_u$ & $\min(0.8d^2\sqrt{f_{ck}E_c},\;0.8\pi d^2 f_u)$ & \placeholder{$Q_u$} kN & IRC 22 Cl. 606.3.1 \\[6pt]
\hline
Fatigue Shear Resistance, Qr & tau\_fn $\times$ (5e6/NSC)\textasciicircum(1/5) & \placeholder{Qr} kN & IRC 22 Cl. 606.3.2 \\[6pt]
\hline
\end{tabularx}
\end{table}

\vspace{1em}
\noindent\textbf{Table 5.15  Shear Connector Spacing}

\begin{table}[H]
\vspace{-6pt}
\begin{tabularx}{\textwidth}{|C{2.5cm}|L{2.8cm}|>{\centering\arraybackslash}X|>{\centering\arraybackslash}X|C{1.5cm}|}
\hline
\textbf{} & \textbf{Criterion} & \textbf{Governing Spacing} & \textbf{Actual Spacing Provided} & \textbf{Status} \\[6pt]
\hline
\multirow{4}{*}{\centering Girder 1 - n} & ULS Shear (SL1) & \placeholder{SL1} mm & \placeholder{S\_prov} mm & PASS \\[6pt]
\cline{2-5}
 & Full Composite (SL2) & \placeholder{SL2} mm & \placeholder{S\_prov} mm & PASS \\[6pt]
\cline{2-5}
 & SLS Fatigue (SR) & \placeholder{SR} mm & \placeholder{S\_prov} mm & PASS \\[6pt]
\cline{2-5}
 & Max Spacing Limit (IRC 22) & $\min(600,\,3t_{slab},\,4h_{stud})$ & \placeholder{limit} mm & PASS \\[6pt]
\hline
\end{tabularx}
\end{table}
\noindent\textit{Note: IRC 22 Cl. 606.4, 606.9. Governing spacing $= \min(S_{L1}, S_{L2}, S_R)$.}

\vspace{1em}
\noindent\textbf{Table 5.16  Transverse Shear and Detailing Checks}

\begin{table}[H]
\vspace{-6pt}
\begin{tabularx}{\textwidth}{|C{3.5cm}|L{5cm}|>{\arraybackslash}X|}
\hline
\multirow{6}{*}{\centering Girder 1 - n} & \textbf{Longitudinal Shear per unit length, $V_L$} & \placeholder{$V_L$} N/mm \\[6pt]
\cline{2-3}
 & \textbf{Transverse Shear Capacity of Slab} & $0.9L \times \sqrt{f_{ck}} + 0.8\,f_{yk}\,A_{st} \geq V_L$ \\[6pt]
\cline{2-3}
 & \textbf{Transverse Shear Check} & PASS / FAIL \\[6pt]
\cline{2-3}
 & \textbf{Min. Transverse Reinforcement, $A_{st,min}$} & \placeholder{$A_{st,min}$} cm²/m \\[6pt]
\cline{2-3}
 & \textbf{Stud Diameter $\leq 2\,t_f$} & \placeholder{$d_{stud}$} mm vs \placeholder{$2t_f$} mm \\[6pt]
\cline{2-3}
 & \textbf{Edge Distance (min 25 mm)} & \placeholder{$e_{dist}$} mm \\[6pt]
\hline
\end{tabularx}
\end{table}
\noindent\textit{Note: IRC 22 Cl. 606.6, 606.10.}

% ===========================
\section{Deck Slab Design}
\label{sec:deck-design}
% ===========================

The reinforced concrete deck slab is designed per IRC~112:2011 (flexure, shear, crack width) and IRC~22:2014 (composite construction). Wheel loads are distributed using Pigeaud's method. The deck is checked for flexure in the transverse and longitudinal directions, punching shear, one-way (beam) shear, crack width, and reinforcement detailing.

\vspace{1em}
\noindent\textbf{Table 5.17(a)  Deck Slab --- Loading and Geometry}

\begin{table}[H]
\vspace{-6pt}
\begin{tabularx}{\textwidth}{|L{5.5cm}|X|}
\hline
\textbf{Effective Span of Deck Slab, $l_{eff}$} & \placeholder{$l_{eff}$} mm (= Girder Spacing $-$ Top Flange Width) \\[6pt]
\hline
\textbf{Deck Thickness, $t_s$} & \placeholder{$t_s$} mm \\[6pt]
\hline
\textbf{Clear Cover (IRC 112 Cl. 15.2)} & \placeholder{cover} mm (Moderate exposure class) \\[6pt]
\hline
\textbf{Dead Load per Unit Area, $w_{DL}$} & \placeholder{$w_{DL}$} kN/m² (self-weight + wearing course) \\[6pt]
\hline
\textbf{IRC 6 Wheel Load (Class A / 70R)} & \placeholder{$P_w$} kN \\[6pt]
\hline
\textbf{Tyre Contact Area (IRC 6 Annex~A)} & \placeholder{$a$} mm $\times$ \placeholder{$b$} mm \\[6pt]
\hline
\textbf{Impact Factor (IRC 6 Cl. 208.2)} & \placeholder{IF} \\[6pt]
\hline
\textbf{Governing Live Load Case} & \placeholder{Class A / 70R Wheeled / 70R Tracked} \\[6pt]
\hline
\end{tabularx}
\end{table}

\vspace{1em}
\noindent\textbf{Table 5.17(b)  Deck Slab --- Flexure Check: Interior Panel (Pigeaud's Method)}

\begin{table}[H]
\vspace{-6pt}
\begin{tabularx}{\textwidth}{|C{3.0cm}|C{3.5cm}|C{3.0cm}|>{\centering\arraybackslash}X|C{1.8cm}|}
\hline
\textbf{Location} & \textbf{Parameter} & \textbf{Formula / Reference} & \textbf{Value} & \textbf{Status} \\[6pt]
\hline
\multirow{5}{*}{\centering At Midspan\\(Sagging)} & Transverse BM (DL), $M_{T,DL}$ & $w_{DL}\,l_{eff}^2/8$ & \placeholder{$M_{T,DL}$} kN-m/m & --- \\[6pt]
\cline{2-5}
 & Transverse BM (LL), $M_{T,LL}$ & Pigeaud coefficients $\times$ $P_w$ & \placeholder{$M_{T,LL}$} kN-m/m & --- \\[6pt]
\cline{2-5}
 & Total Design BM, $M_{u,sag}$ & 1.35 DL + 1.5 LL & \placeholder{$M_{u,sag}$} kN-m/m & --- \\[6pt]
\cline{2-5}
 & Effective depth, $d$ & $t_s - c_{nom} - \phi/2$ & \placeholder{$d$} mm & --- \\[6pt]
\cline{2-5}
 & Moment Capacity, $M_{Rd}$ & IRC 112 Cl. 12.2 & \placeholder{$M_{Rd}$} kN-m/m & PASS / FAIL \\[6pt]
\hline
\multirow{3}{*}{\centering At Support\\(Hogging)} & Total Design BM, $M_{u,hog}$ & 1.35 DL + 1.5 LL (at support) & \placeholder{$M_{u,hog}$} kN-m/m & --- \\[6pt]
\cline{2-5}
 & Required Top Steel, $A_{st,top}$ & $M_u / (0.87\,f_y\,d)$ & \placeholder{$A_{st,top}$} mm²/m & --- \\[6pt]
\cline{2-5}
 & Moment Capacity, $M_{Rd}$ & IRC 112 Cl. 12.2 & \placeholder{$M_{Rd}$} kN-m/m & PASS / FAIL \\[6pt]
\hline
\end{tabularx}
\end{table}
\noindent\textit{Note: IRC 112 Cl. 12.2. Distribution (longitudinal) reinforcement designed for 20\% of main steel moment (IRC 21 Cl. 305.18).}

\vspace{1em}
\noindent\textbf{Table 5.17(c)  Deck Slab --- Cantilever Overhang Flexure Check}

\begin{table}[H]
\vspace{-6pt}
\begin{tabularx}{\textwidth}{|L{5.5cm}|C{3.5cm}|>{\centering\arraybackslash}X|C{2cm}|}
\hline
\textbf{Parameter} & \textbf{Formula} & \textbf{Value} & \textbf{Status} \\[6pt]
\hline
Overhang Length, $l_{oh}$ & --- & \placeholder{$l_{oh}$} mm & --- \\[6pt]
\hline
Crash Barrier Load Moment & $P_{CB} \times l_{oh}$ & \placeholder{$M_{CB}$} kN-m/m & --- \\[6pt]
\hline
Dead Load Moment & $w_{DL}\,l_{oh}^2/2$ & \placeholder{$M_{DL,oh}$} kN-m/m & --- \\[6pt]
\hline
Live Load Moment (eccentric wheel) & Wheel load $\times$ eccentricity & \placeholder{$M_{LL,oh}$} kN-m/m & --- \\[6pt]
\hline
Total Hogging Moment, $M_{u,oh}$ & 1.35 DL + 1.5 LL + 1.5 CB & \placeholder{$M_{u,oh}$} kN-m/m & --- \\[6pt]
\hline
Moment Capacity (top steel), $M_{Rd,oh}$ & IRC 112 Cl. 12.2 & \placeholder{$M_{Rd,oh}$} kN-m/m & PASS / FAIL \\[6pt]
\hline
\end{tabularx}
\end{table}
\noindent\textit{Note: IRC 6 Cl. 206.4 crash barrier loads applied at kerb face; IRC 112 Cl. 12.2 flexure.}

\vspace{1em}
\noindent\textbf{Table 5.17(d)  Deck Slab --- Punching Shear Check (IRC~112 Cl.~10.4.6)}

\begin{table}[H]
\vspace{-6pt}
\begin{tabularx}{\textwidth}{|L{5.5cm}|C{3.5cm}|>{\centering\arraybackslash}X|C{2cm}|}
\hline
\textbf{Parameter} & \textbf{Formula / Reference} & \textbf{Value} & \textbf{Status} \\[6pt]
\hline
Design Wheel Load (ULS), $V_{Ed}$ & $\gamma_Q \times P_w \times (1 + IF)$ & \placeholder{$V_{Ed}$} kN & --- \\[6pt]
\hline
Tyre Contact Area & $a \times b$ (IRC 6 Annex A) & \placeholder{$a \times b$} mm & --- \\[6pt]
\hline
Loaded Area at mid-depth, $b_0$ & Dispersed at 45° to $d/2$ from surface & \placeholder{$b_0$} mm & --- \\[6pt]
\hline
Control Perimeter, $u_1$ & At $2d$ from loaded area (IRC 112) & \placeholder{$u_1$} mm & --- \\[6pt]
\hline
Punching Shear Stress, $v_{Ed}$ & $V_{Ed}/(u_1 \times d)$ & \placeholder{$v_{Ed}$} N/mm² & --- \\[6pt]
\hline
Punching Resistance, $v_{Rd,c}$ & IRC 112 Cl. 10.4.6 & \placeholder{$v_{Rd,c}$} N/mm² & --- \\[6pt]
\hline
Punching Shear Check & $v_{Ed} \leq v_{Rd,c}$ & \placeholder{UR} & PASS / FAIL \\[6pt]
\hline
\end{tabularx}
\end{table}
\noindent\textit{Note: Punching shear reinforcement not typically required for deck slabs with $d \geq 200$ mm and adequate longitudinal reinforcement.}

\vspace{1em}
\noindent\textbf{Table 5.17(e)  Crack Width Check (Deck Slab)}

\begin{table}[H]
\vspace{-6pt}
\begin{tabularx}{\textwidth}{|C{7cm}|>{\arraybackslash}X|}
\hline
\textbf{Min. Reinforcement for Crack Control, $A_{s,min}$} & \placeholder{$A_{s,min}$} cm² [IRC 22 Cl. 604.4] \\[6pt]
\hline
\textbf{Provided Reinforcement} & \placeholder{As\_prov} cm² \\[6pt]
\hline
\textbf{Max. Permissible Crack Width} & 0.3 mm (IRC 112 Cl. 12.3.3) \\[6pt]
\hline
\textbf{Calculated Crack Width, wk} & \placeholder{wk} mm \\[6pt]
\hline
\textbf{Crack Width Check} & PASS / FAIL \\[6pt]
\hline
\end{tabularx}
\end{table}

\vspace{1em}
\noindent\textbf{Table 5.17(f)  One-Way (Beam) Shear Check (Deck Slab)}

\begin{table}[H]
\vspace{-6pt}
\begin{tabularx}{\textwidth}{|L{5.5cm}|C{3.5cm}|>{\centering\arraybackslash}X|C{2cm}|}
\hline
\textbf{Parameter} & \textbf{Formula / Reference} & \textbf{Value} & \textbf{Status} \\[6pt]
\hline
Design Shear per unit width, $V_{Ed}$ & ULS load combination & \placeholder{$V_{Ed}$} kN/m & --- \\[6pt]
\hline
Effective depth, $d$ & $t_s - c_{nom} - \phi/2$ & \placeholder{$d$} mm & --- \\[6pt]
\hline
Size factor, $k$ & $1 + \sqrt{200/d} \leq 2.0$ & \placeholder{$k$} & --- \\[6pt]
\hline
Long.\ reinforcement ratio, $\rho_l$ & $A_{sl}/(b \cdot d) \leq 0.02$ & \placeholder{$\rho_l$} & --- \\[6pt]
\hline
Shear resistance (no stirrups), $V_{Rd,c}$ & IRC 112 Cl. 10.3.2: $[0.12\,k\,(80\,\rho_l\,f_{ck})^{1/3}]\,b\,d$ & \placeholder{$V_{Rd,c}$} kN/m & --- \\[6pt]
\hline
One-Way Shear Check & $V_{Ed} \leq V_{Rd,c}$ & \placeholder{UR} & PASS / FAIL \\[6pt]
\hline
\end{tabularx}
\end{table}
\noindent\textit{Note: IRC 112 Cl. 10.3.2. Shear reinforcement not provided in deck slabs; capacity relies on concrete and main reinforcement.}

\vspace{1em}
\noindent\textbf{Table 5.17(g)  Reinforcement Detailing Summary (Deck Slab)}

\begin{table}[H]
\vspace{-6pt}
\begin{tabularx}{\textwidth}{|L{5.5cm}|>{\centering\arraybackslash}X|>{\centering\arraybackslash}X|C{1.8cm}|}
\hline
\textbf{Parameter} & \textbf{Required / Limit} & \textbf{Provided} & \textbf{Status} \\[6pt]
\hline
\multicolumn{4}{|l|}{\textbf{Main Reinforcement --- Bottom (Transverse)}} \\[6pt]
\hline
Required Area, $A_{st,req}$ (mm²/m) & \placeholder{$A_{st,req}$} mm²/m & \placeholder{$A_{st,prov}$} mm²/m & PASS \\[6pt]
\hline
Bar Diameter $\times$ Spacing & $\phi \geq 10$ mm (IRC 112) & \placeholder{$\phi$} mm @ \placeholder{$s$} mm c/c & PASS \\[6pt]
\hline
Min.\ Reinforcement $A_{s,min}$ (IRC 112 Cl. 16.3.1) & $0.0013\,b\,d$ & \placeholder{$A_{s,min}$} mm²/m & PASS \\[6pt]
\hline
Max.\ Bar Spacing (IRC 112 Cl. 16.3.2) & $\leq \min(2t_s,\;250\text{ mm})$ & \placeholder{$s$} mm & PASS \\[6pt]
\hline
\multicolumn{4}{|l|}{\textbf{Distribution Reinforcement --- Longitudinal}} \\[6pt]
\hline
Required Area, $A_{st,dist}$ (mm²/m) & $\geq 20\%$ of main steel & \placeholder{$A_{st,dist}$} mm²/m & PASS \\[6pt]
\hline
\multicolumn{4}{|l|}{\textbf{Top Reinforcement (Support / Cantilever Overhang)}} \\[6pt]
\hline
Required Area, $A_{st,top}$ (mm²/m) & \placeholder{$A_{st,req,top}$} mm²/m & \placeholder{$A_{st,top}$} mm²/m & PASS \\[6pt]
\hline
\multicolumn{4}{|l|}{\textbf{Cover and Detailing}} \\[6pt]
\hline
Clear Cover (IRC 112 Cl. 15.2) & 40 mm (Moderate exposure) & \placeholder{cover} mm & PASS \\[6pt]
\hline
\end{tabularx}
\end{table}
\noindent\textit{Note: IRC 112 Cl. 16.3, IS 456 Cl. 26.5. All reinforcement provisions satisfy strength and detailing requirements.}

% ===========================
\section{Cross Bracing Design}
\label{sec:cross-bracing}
% ===========================

Cross bracing between adjacent plate girders provides lateral stability during construction, resists transverse loads (wind, seismic, braking) in service, and prevents lateral torsional buckling of the girders. Members are designed per IS~800:2007 Cl.~7 (compression) and Cl.~6 (tension). Forces are derived from the grillage model under the governing load combination LC-ULS-2 (DL + LL + WL).

\vspace{1em}
\noindent\textbf{Table 5.20(a)  Cross Bracing --- Member Forces and Section Properties}

\vspace{0.4em}
\noindent
\setlength{\tabcolsep}{4pt}
\begin{longtable}{|C{2.0cm}|C{2.0cm}|C{2.2cm}|C{2.0cm}|C{1.6cm}|C{1.6cm}|C{1.6cm}|}
\hline
\textbf{Panel} & \textbf{Member} & \textbf{Section} & \textbf{$P_u$ (kN)} & \textbf{Nature} & \textbf{$A_g$ (mm²)} & \textbf{$r_{min}$ (mm)} \\[6pt]
\hline
\multirow{3}{*}{\centering G1--G2} & Diagonal & \placeholder{ISA} & \placeholder{$P_u$} & C / T & \placeholder{$A_g$} & \placeholder{$r$} \\[6pt]
\cline{2-7}
 & Top chord & \placeholder{ISA} & \placeholder{$P_u$} & C / T & \placeholder{$A_g$} & \placeholder{$r$} \\[6pt]
\cline{2-7}
 & Bottom chord & \placeholder{ISA} & \placeholder{$P_u$} & C / T & \placeholder{$A_g$} & \placeholder{$r$} \\[6pt]
\hline
\multirow{3}{*}{\centering G2--G3} & Diagonal & \placeholder{ISA} & \placeholder{$P_u$} & C / T & \placeholder{$A_g$} & \placeholder{$r$} \\[6pt]
\cline{2-7}
 & Top chord & \placeholder{ISA} & \placeholder{$P_u$} & C / T & \placeholder{$A_g$} & \placeholder{$r$} \\[6pt]
\cline{2-7}
 & Bottom chord & \placeholder{ISA} & \placeholder{$P_u$} & C / T & \placeholder{$A_g$} & \placeholder{$r$} \\[6pt]
\hline
\multirow{3}{*}{\centering G3--G4} & Diagonal & \placeholder{ISA} & \placeholder{$P_u$} & C / T & \placeholder{$A_g$} & \placeholder{$r$} \\[6pt]
\cline{2-7}
 & Top chord & \placeholder{ISA} & \placeholder{$P_u$} & C / T & \placeholder{$A_g$} & \placeholder{$r$} \\[6pt]
\cline{2-7}
 & Bottom chord & \placeholder{ISA} & \placeholder{$P_u$} & C / T & \placeholder{$A_g$} & \placeholder{$r$} \\[6pt]
\hline
\multirow{3}{*}{\centering G4--G5} & Diagonal & \placeholder{ISA} & \placeholder{$P_u$} & C / T & \placeholder{$A_g$} & \placeholder{$r$} \\[6pt]
\cline{2-7}
 & Top chord & \placeholder{ISA} & \placeholder{$P_u$} & C / T & \placeholder{$A_g$} & \placeholder{$r$} \\[6pt]
\cline{2-7}
 & Bottom chord & \placeholder{ISA} & \placeholder{$P_u$} & C / T & \placeholder{$A_g$} & \placeholder{$r$} \\[6pt]
\hline
\end{longtable}
\noindent\textit{Note: C = Compression; T = Tension. Governing load combination: LC-ULS-2 (DL + LL + WL). $A_g$ = gross cross-sectional area; $r_{min}$ = minimum radius of gyration.}

\vspace{1em}
\noindent\textbf{Table 5.20(b)  Cross Bracing --- Slenderness Ratio Check (IS~800 Cl.~3.8 \& Table~3)}

\begin{table}[H]
\vspace{-6pt}
\begin{tabularx}{\textwidth}{|C{2.2cm}|C{2.2cm}|C{2.5cm}|C{2.5cm}|C{2.5cm}|>{\centering\arraybackslash}X|}
\hline
\textbf{Panel} & \textbf{Member} & \textbf{Nature} & \textbf{Eff.\ Length $KL$ (mm)} & \textbf{$KL/r$} & \textbf{Limit / Status} \\[6pt]
\hline
\multirow{3}{*}{\centering G1--G2} & Diagonal & C & \placeholder{$KL$} & \placeholder{$KL/r$} & 250 --- PASS \\[6pt]
\cline{2-6}
 & Top chord & C & \placeholder{$KL$} & \placeholder{$KL/r$} & 250 --- PASS \\[6pt]
\cline{2-6}
 & Bottom chord & T & \placeholder{$KL$} & \placeholder{$KL/r$} & 400 --- PASS \\[6pt]
\hline
\multirow{3}{*}{\centering G2--G3} & Diagonal & C & \placeholder{$KL$} & \placeholder{$KL/r$} & 250 --- PASS \\[6pt]
\cline{2-6}
 & Top chord & C & \placeholder{$KL$} & \placeholder{$KL/r$} & 250 --- PASS \\[6pt]
\cline{2-6}
 & Bottom chord & T & \placeholder{$KL$} & \placeholder{$KL/r$} & 400 --- PASS \\[6pt]
\hline
\multirow{3}{*}{\centering G3--G4} & Diagonal & C & \placeholder{$KL$} & \placeholder{$KL/r$} & 250 --- PASS \\[6pt]
\cline{2-6}
 & Top chord & C & \placeholder{$KL$} & \placeholder{$KL/r$} & 250 --- PASS \\[6pt]
\cline{2-6}
 & Bottom chord & T & \placeholder{$KL$} & \placeholder{$KL/r$} & 400 --- PASS \\[6pt]
\hline
\multirow{3}{*}{\centering G4--G5} & Diagonal & C & \placeholder{$KL$} & \placeholder{$KL/r$} & 250 --- PASS \\[6pt]
\cline{2-6}
 & Top chord & C & \placeholder{$KL$} & \placeholder{$KL/r$} & 250 --- PASS \\[6pt]
\cline{2-6}
 & Bottom chord & T & \placeholder{$KL$} & \placeholder{$KL/r$} & 400 --- PASS \\[6pt]
\hline
\end{tabularx}
\end{table}
\noindent\textit{Note: IS 800 Table 3. Limit = 250 for compression members, 400 for tension members. $K = 1.0$ for members with both ends pinned.}

\vspace{1em}
\noindent\textbf{Table 5.20(c)  Cross Bracing --- Compression Capacity Check (IS~800 Cl.~7)}

\begin{table}[H]
\vspace{-6pt}
\begin{tabularx}{\textwidth}{|C{2.5cm}|C{3.5cm}|C{3.5cm}|>{\centering\arraybackslash}X|C{1.8cm}|}
\hline
\textbf{} & \textbf{Parameter} & \textbf{Formula} & \textbf{Value} & \textbf{Status} \\[6pt]
\hline
\multirow{8}{*}{\centering Diagonal\\(typical)} & Euler Critical Stress, $f_{cc}$ & $\pi^2 E / (KL/r)^2$ & \placeholder{$f_{cc}$} MPa & --- \\[6pt]
\cline{2-5}
 & Non-dim.\ Slenderness, $\bar{\lambda}$ & $\sqrt{f_y / f_{cc}}$ & \placeholder{$\bar{\lambda}$} & --- \\[6pt]
\cline{2-5}
 & Imperfection Factor, $\alpha$ & Buckling curve `c' (IS 800 Table 7) & 0.49 & --- \\[6pt]
\cline{2-5}
 & $\phi$ factor & $0.5[1 + \alpha(\bar{\lambda} - 0.2) + \bar{\lambda}^2]$ & \placeholder{$\phi$} & --- \\[6pt]
\cline{2-5}
 & Stress Reduction Factor, $\chi$ & $1/[\phi + \sqrt{\phi^2 - \bar{\lambda}^2}] \leq 1$ & \placeholder{$\chi$} & --- \\[6pt]
\cline{2-5}
 & Design Comp.\ Stress, $f_{cd}$ & $\chi \times f_y / \gamma_{M0}$ & \placeholder{$f_{cd}$} MPa & --- \\[6pt]
\cline{2-5}
 & Compression Capacity, $P_d$ & $A_e \times f_{cd}$ & \placeholder{$P_d$} kN & --- \\[6pt]
\cline{2-5}
 & Utilization Ratio, $P_u / P_d$ & --- & \placeholder{UR} & $\leq 1.0$ \\[6pt]
\hline
\end{tabularx}
\end{table}
\noindent\textit{Note: IS 800 Cl. 7.1.2. Effective area $A_e$ accounts for single-leg connection (shear lag) per IS 800 Cl. 7.5.1.2. $\gamma_{M0} = 1.10$.}

\vspace{1em}
\noindent\textbf{Table 5.20(d)  Cross Bracing --- Tension Capacity Check (IS~800 Cl.~6)}

\begin{table}[H]
\vspace{-6pt}
\begin{tabularx}{\textwidth}{|C{2.5cm}|C{3.5cm}|C{3.5cm}|>{\centering\arraybackslash}X|C{1.8cm}|}
\hline
\textbf{} & \textbf{Parameter} & \textbf{Formula} & \textbf{Value} & \textbf{Status} \\[6pt]
\hline
\multirow{6}{*}{\centering Bottom chord\\(typical)} & Gross Yielding, $T_{dg}$ & $A_g \times f_y / \gamma_{M0}$ & \placeholder{$T_{dg}$} kN & --- \\[6pt]
\cline{2-5}
 & Net Section Area, $A_n$ & $A_g - n_h \times d_h \times t$ & \placeholder{$A_n$} mm² & --- \\[6pt]
\cline{2-5}
 & Net Rupture, $T_{dn}$ & $0.9 A_n f_u / \gamma_{M1}$ & \placeholder{$T_{dn}$} kN & --- \\[6pt]
\cline{2-5}
 & Block Shear, $T_{db}$ & IS 800 Cl. 6.4.1 & \placeholder{$T_{db}$} kN & --- \\[6pt]
\cline{2-5}
 & Design Tensile Strength, $T_d$ & $\min(T_{dg},\,T_{dn},\,T_{db})$ & \placeholder{$T_d$} kN & --- \\[6pt]
\cline{2-5}
 & Utilization Ratio, $T_u / T_d$ & --- & \placeholder{UR} & $\leq 1.0$ \\[6pt]
\hline
\end{tabularx}
\end{table}
\noindent\textit{Note: IS 800 Cl. 6.1--6.4. $d_h$ = bolt hole diameter; $n_h$ = number of bolt holes; $t$ = angle leg thickness. $\gamma_{M0} = 1.10$; $\gamma_{M1} = 1.25$.}

\vspace{1em}
\noindent\textbf{Table 5.20(e)  Cross Bracing Design --- Capacity Summary}

\begin{table}[H]
\vspace{-6pt}
\begin{tabularx}{\textwidth}{|C{3.3cm}|C{3.2cm}|C{3.2cm}|>{\centering\arraybackslash}X|C{2.3cm}|}
\hline
\textbf{} & \textbf{Member} & \textbf{Section} & \textbf{Demand (kN)} & \textbf{Capacity (kN)} \\[6pt]
\hline
\multirow{3}{*}{\centering Girder 1 -- 2} & Brace diagonal (typical) & \placeholder{ISA section} & \placeholder{P\_u} & \placeholder{P\_d} --- PASS \\[6pt]
\cline{2-5}
 & Top chord & \placeholder{ISA section} & \placeholder{P\_u} & \placeholder{P\_d} --- PASS \\[6pt]
\cline{2-5}
 & Bottom chord & \placeholder{ISA section} & \placeholder{P\_u} & \placeholder{P\_d} --- PASS \\[6pt]
\hline
\multirow{3}{*}{\centering \shortstack{Girder 2 -- 3\\and so on}} & Brace diagonal (typical) & \placeholder{ISA section} & \placeholder{P\_u} & \placeholder{P\_d} --- PASS \\[6pt]
\cline{2-5}
 & Top chord & \placeholder{ISA section} & \placeholder{P\_u} & \placeholder{P\_d} --- PASS \\[6pt]
\cline{2-5}
 & Bottom chord & \placeholder{ISA section} & \placeholder{P\_u} & \placeholder{P\_d} --- PASS \\[6pt]
\hline
\end{tabularx}
\end{table}
\noindent\textit{Note: Designed per IS 800 Cl. 7 (compression) and Cl. 6 (tension). OsdagBridge cross-bracing module used.}

% ===========================
\section{End Diaphragm Design}
\label{sec:end-diaphragm}
% ===========================

End diaphragms at the supports transfer transverse loads to the bearings, restrain the bottom flanges against lateral displacement, and maintain the girder cross-section geometry during construction and in service. They are designed per IS~800:2007 and IRC~24:2010 Cl.~507.

\vspace{1em}
\noindent\textbf{Table 5.21(a)  End Diaphragm --- Member Properties and Forces}

\begin{table}[H]
\vspace{-6pt}
\begin{tabularx}{\textwidth}{|L{5.5cm}|X|}
\hline
\textbf{End Diaphragm Type} & \placeholder{K-Bracing / X-Bracing / Rolled Beam / Welded} \\[6pt]
\hline
\textbf{Section Designation} & \placeholder{e.g. ISA 150$\times$150$\times$12 / ISMB 300} \\[6pt]
\hline
\textbf{Diaphragm Span (c/c girder spacing)} & \placeholder{span} mm \\[6pt]
\hline
\textbf{Governing Load Combination} & LC-ULS-1 (DL + LL) \\[6pt]
\hline
\textbf{Max.\ Bending Moment, $M_u$} & \placeholder{$M_u$} kN-m \\[6pt]
\hline
\textbf{Max.\ Shear Force, $V_u$} & \placeholder{$V_u$} kN \\[6pt]
\hline
\textbf{Axial Force, $P_u$ (diagonal members)} & \placeholder{$P_u$} kN \\[6pt]
\hline
\end{tabularx}
\end{table}

\vspace{1em}
\noindent\textbf{Table 5.21(b)  End Diaphragm Design --- Capacity Checks}

\begin{table}[H]
\vspace{-6pt}
\begin{tabularx}{\textwidth}{|C{4cm}|L{5cm}|>{\arraybackslash}X|}
\hline
\multirow{7}{*}{\centering\textbf{\shortstack{End Diaphragm\\(G1--G2 and\\G2--G3, etc.)}}} & \textbf{Section Designation} & \placeholder{Section} \\[6pt]
\cline{2-3}
 & \textbf{Moment Demand, $M_u$} & \placeholder{$M_u$} kN-m \\[6pt]
\cline{2-3}
 & \textbf{Moment Capacity, $M_d$} & \placeholder{$M_d$} kN-m (IS 800 Cl. 8.2) \\[6pt]
\cline{2-3}
 & \textbf{Shear Demand, $V_u$} & \placeholder{$V_u$} kN \\[6pt]
\cline{2-3}
 & \textbf{Shear Capacity, $V_d$} & \placeholder{$V_d$} kN (IS 800 Cl. 8.4) \\[6pt]
\cline{2-3}
 & \textbf{Max.\ Utilization Ratio} & \placeholder{UR} \\[6pt]
\cline{2-3}
 & \textbf{Status} & PASS / FAIL \\[6pt]
\hline
\end{tabularx}
\end{table}
\noindent\textit{Note: IS 800:2007 Cl. 8.2 (moment capacity), Cl. 8.4 (shear capacity). IRC 24:2010 Cl. 507 (diaphragm requirements).}
\vspace{1em}
\noindent\textbf{Table 5.22  Overall Design Check Summary --- All Members}

\begin{table}[H]
\vspace{-6pt}
\begin{tabularx}{\textwidth}{|C{4cm}|C{3cm}|C{2.5cm}|C{2.5cm}|>{\centering\arraybackslash}X|}
\hline
\textbf{Member / Check} & \textbf{Governing Load Combo} & \textbf{Demand} & \textbf{Capacity} & \textbf{UR} \\[6pt]
\hline
Girder --- Moment & LC-ULS-1 & \placeholder{$M_u$} & \placeholder{$M_d$} & \placeholder{UR} \\[6pt]
\hline
Girder --- Shear & LC-ULS-1 & \placeholder{$V_u$} & \placeholder{$V_d$} & \placeholder{UR} \\[6pt]
\hline
Girder --- LTB (constr.) & LC-ULS-1 & \placeholder{$M_u$} & \placeholder{$M_b$} & \placeholder{UR} \\[6pt]
\hline
Girder --- Deflection & LC-SLS-1 & \placeholder{δ} & \placeholder{δ\_allow} & \placeholder{UR} \\[6pt]
\hline
Girder --- Stress & LC-SLS-1 & \placeholder{sigma} & \placeholder{sigma\_allow} & \placeholder{UR} \\[6pt]
\hline
Girder --- Fatigue & LC-FAT-1 & \placeholder{f\_range} & \placeholder{ffd} & \placeholder{UR} \\[6pt]
\hline
Shear Connectors & LC-ULS-1 / FAT & \placeholder{$V_L$} & \placeholder{Qu/spacing} & \placeholder{UR} \\[6pt]
\hline
Transverse Shear (slab) & LC-ULS-1 & \placeholder{$V_L$} & \placeholder{capacity} & \placeholder{UR} \\[6pt]
\hline
Crack Width (slab) & LC-SLS-1 & \placeholder{wk} & 0.3 mm & \placeholder{UR} \\[6pt]
\hline
Deck --- Flexure (sagging) & LC-ULS-1 & \placeholder{$M_{u,sag}$} & \placeholder{$M_{Rd}$} & \placeholder{UR} \\[6pt]
\hline
Deck --- Flexure (hogging) & LC-ULS-1 & \placeholder{$M_{u,hog}$} & \placeholder{$M_{Rd}$} & \placeholder{UR} \\[6pt]
\hline
Deck --- Cantilever Overhang & LC-ULS-1 & \placeholder{$M_{u,oh}$} & \placeholder{$M_{Rd,oh}$} & \placeholder{UR} \\[6pt]
\hline
Deck --- Punching Shear & LC-ULS-1 & \placeholder{$v_{Ed}$} & \placeholder{$v_{Rd,c}$} & \placeholder{UR} \\[6pt]
\hline
Deck --- One-Way Shear & LC-ULS-1 & \placeholder{$V_{Ed}$} & \placeholder{$V_{Rd,c}$} & \placeholder{UR} \\[6pt]
\hline
Cross Bracing --- Compression & LC-ULS-2 & \placeholder{$P_u$} & \placeholder{$P_d$} & \placeholder{UR} \\[6pt]
\hline
Cross Bracing --- Tension & LC-ULS-2 & \placeholder{$T_u$} & \placeholder{$T_d$} & \placeholder{UR} \\[6pt]
\hline
Cross Bracing --- Slenderness & --- & \placeholder{$KL/r$} & 250 / 400 & PASS \\[6pt]
\hline
End Diaphragm --- Moment & LC-ULS-1 & \placeholder{$M_u$} & \placeholder{$M_d$} & \placeholder{UR} \\[6pt]
\hline
End Diaphragm --- Shear & LC-ULS-1 & \placeholder{$V_u$} & \placeholder{$V_d$} & \placeholder{UR} \\[6pt]
\hline
Inter. Stiffener ($I_s$) & --- & \placeholder{$I_{s,req}$} & \placeholder{$I_{s,prov}$} & PASS \\[6pt]
\hline
\end{tabularx}
\end{table}
\noindent\textit{Note: UR = Demand / Capacity. All values $\leq 1.0$ indicate passing checks. The governing check for each component is highlighted in the individual design check sections above.}

"""


# Chapters 6-9: Drawings, Quantities, Logs, References


def _fig_embed(path, caption, width=r'0.9\textwidth'):
    """Embed a real figure when path is provided (already copied); otherwise use an fbox placeholder."""
    if path:
        p = path.replace('\\', '/')
        return (r'\begin{figure}[H]' + '\n'
                r'\centering' + '\n'
                r'\includegraphics[width=' + width + ']{' + p + '}\n'
                r'\caption*{' + caption + '}\n'
                r'\end{figure}')
    # fbox placeholder — matches template exactly
    return (r'\noindent\fbox{\parbox{0.97\textwidth}{' + '\n'
            r'\textit{[ PLACEHOLDER: ' + caption + r' ]}' + '\n'
            r'}}')


def ch6_drawings(fig_paths):
    """Chapter 6 – Drawings and Visualizations.

    Mirrors the exact section/subsection structure and fbox-placeholder style
    from the LaTeX template. Real figures are embedded when available;
    otherwise the fbox placeholder text is shown.
    """

    def _sec_fig(path, placeholder_text, caption=None):
        """Render figure or fbox placeholder. caption is used only for real images."""
        if path:
            p = path.replace('\\', '/')
            cap = caption or placeholder_text
            return (r'\begin{figure}[H]' + '\n'
                    r'\centering' + '\n'
                    r'\includegraphics[width=0.9\textwidth]{' + p + '}\n'
                    r'\caption*{' + cap + '}\n'
                    r'\end{figure}')
        return (r'\noindent\fbox{\parbox{0.97\textwidth}{' + '\n'
                r'\textit{[ PLACEHOLDER: ' + placeholder_text + r' ]}' + '\n'
                r'}}')

    cs   = _sec_fig(fig_paths.get('cross_section'),
                    'FIGURE 6.1 --- Annotated cross-section of the bridge deck showing: '
                    'overall width, carriageway, footpath, crash barriers, median (if any), '
                    'no. of girders, girder spacing, deck overhang, deck thickness, and '
                    'wearing course thickness. Label all key dimensions.',
                    'Figure 6.1 -- Typical Cross Section')

    elev = _sec_fig(fig_paths.get('longitudinal_elevation'),
                    'FIGURE 6.2 --- Side elevation of the full bridge span showing: '
                    'span length, support locations, bearing positions, intermediate '
                    'stiffener locations (marked as tick marks), and cross bracing positions.',
                    'Figure 6.2 -- Longitudinal Elevation')

    g3d  = _sec_fig(fig_paths.get('girder_3d'),
                    'FIGURE 6.3 --- 3D isometric view of a single plate girder (full span) '
                    'showing: web, top and bottom flanges, intermediate transverse stiffeners, '
                    'end panel stiffeners, longitudinal stiffeners (if required), and shear '
                    'studs on the top flange. Use OsdagBridge CAD output.',
                    'Figure 6.3 -- 3D View of Single Plate Girder')

    gtop = _sec_fig(fig_paths.get('girder_top'),
                    'FIGURE 6.4 --- Plan (top) view of the girder showing: flange widths, '
                    'stiffener spacing pattern, shear stud layout zones (dense near supports, '
                    'sparser at midspan).',
                    'Figure 6.4 -- Top View of Girder')

    gend = _sec_fig(fig_paths.get('girder_end'),
                    'FIGURE 6.5 --- Front and side views of the end panel region showing: '
                    'end panel stiffener dimensions, web thickness, flange details, and weld '
                    'positions.',
                    'Figure 6.5 -- Front and Side Views (End Panel Detail)')

    sup3d = _sec_fig(fig_paths.get('final_geometry'),
                     'FIGURE 6.6 --- 3D view of the complete superstructure: all girders in '
                     'position, cross bracing between girders, end diaphragms at supports, and '
                     'deck slab (shown as transparent or ghost outline). This gives the '
                     'stakeholder a comprehensive picture of what is being built.',
                     'Figure 6.6 -- Overall 3D Bridge Superstructure')

    scon = _sec_fig(fig_paths.get('shear_connector'),
                    'FIGURE 6.7 --- Close-up detail of the top flange showing shear stud '
                    'placement: stud diameter, stud height, longitudinal spacing pattern, '
                    'transverse spacing, and edge distances. Show both plan and elevation views.',
                    'Figure 6.7 -- Shear Connector Layout Detail')

    cbrc = _sec_fig(fig_paths.get('cross_bracing'),
                    'FIGURE 6.8 --- 3D detail of a typical cross-bracing panel between two '
                    'adjacent girders: brace type (K or X), section designation, connection '
                    'geometry. Elevation and plan view.',
                    'Figure 6.8 -- Cross Bracing Detail')

    return (r"""
\chapter{Drawings and Visualizations}
\label{ch:drawings}

This section presents CAD-generated views of the designed bridge and its components. All views are generated automatically by OsdagBridge using pythonOCC.

\section{Bridge Configuration and Layout}
\label{sec:bridge-layout}

\subsection{Typical Cross Section}
\label{subsec:cross-section}

"""
            + cs + r"""

\vspace{1em}

\subsection{Longitudinal Elevation}
\label{subsec:elevation}

"""
            + elev + r"""

\vspace{1em}

\section{Plate Girder --- Detailed Views}
\label{sec:girder-views}

\subsection{3D View of Single Plate Girder}
\label{subsec:3d-girder}

"""
            + g3d + r"""

\vspace{1em}

\subsection{Top View of Girder}
\label{subsec:top-view}

"""
            + gtop + r"""

\vspace{1em}

\subsection{Front and Side Views (End Panel Detail)}
\label{subsec:end-panel}

"""
            + gend + r"""

\vspace{1em}

\section{Overall 3D Bridge Superstructure}
\label{sec:3d-structure}

"""
            + sup3d + r"""

\vspace{1em}

\section{Shear Connector Layout Detail}
\label{sec:connector-layout}

"""
            + scon + r"""

\vspace{1em}

\section{Cross Bracing Detail}
\label{sec:bracing-detail}

"""
            + cbrc + '\n')


def ch7_quantities(inp):
    return r"""
\chapter{Material Take-off \& Quantity Summary}
\label{ch:material-takeoff}

\noindent\textbf{Table 7.1  Bill of Materials (Steel tonnage for girders, bracing, stiffeners, studs, etc.; Concrete volume; Reinforcement)}

\begin{table}[H]
\begin{tabularx}{\textwidth}{|>{\centering\arraybackslash}C{1cm}|X|>{\centering\arraybackslash}C{2cm}|>{\centering\arraybackslash}C{2cm}|>{\centering\arraybackslash}C{2cm}|}
\hline
\textbf{S.N.} & \textbf{Item Description} & \textbf{Unit} & \textbf{Quantity} & \textbf{Remarks} \\
\hline
1 & Structural Steel (IS 2062) for Girders & MT & """ + str(inp.get("steel_girders_mt", _ph("steel_girders_mt"))) + r""" & \\
\hline
2 & Structural Steel for Cross Bracings & MT & """ + str(inp.get("steel_bracing_mt", _ph("steel_bracing_mt"))) + r""" & \\
\hline
3 & Concrete (M40) for Deck Slab & Cu.m & """ + str(inp.get("concrete_deck_cum", _ph("concrete_deck_cum"))) + r""" & \\
\hline
4 & Reinforcement Steel (Fe 500) & MT & """ + str(inp.get("rebar_deck_mt", _ph("rebar_deck_mt"))) + r""" & \\
\hline
5 & Shear Stud Connectors & Nos & """ + str(inp.get("shear_studs_nos", _ph("shear_studs_nos"))) + r""" & \\
\hline
\end{tabularx}
\end{table}
"""


def ch8_design_log(log_entries: List[str]) -> str:
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
                    continue  # skip lines without a known level — Osdag pattern
    if not lines_tex:
        lines_tex.append(r'\textit{No design log entries recorded.}')
    log_body = '\n'.join(lines_tex)

    return (
        r"""
\chapter{Design Log \& Verification}
\label{ch:verification}

This section provides references to verification used to calibrate the OsdagBridge
design modules, and notes the limitations of the current software version.

\section{Verification}
\label{sec:verification}

\begin{flushleft}
""" + log_body + r"""
\end{flushleft}

\vspace{1em}
\begin{itemize}
\item List of all code clauses used (IRC 5, 6, 22, 24, IS 800, IRC 112, IRC SP 114, etc.)
\item Software version \& build date: OsdagBridge
\item Note on assumptions (if any) and recommendations for site-specific checks
\end{itemize}

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
"""
    )


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
    grillage:        Optional[str] = None
    plan:            Optional[str] = None
    cross_section:   Optional[str] = None
    final_geometry:  Optional[str] = None
    longitudinal_elevation: Optional[str] = None
    girder_3d:       Optional[str] = None
    girder_top:      Optional[str] = None
    girder_end:      Optional[str] = None
    bm_envelope:     Optional[str] = None
    sf_envelope:     Optional[str] = None
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
    backend:          Any = field(default=None)
    backend_results:  dict = field(default_factory=dict)


@dataclass
class ReportResult:
    pdf_path: Optional[str]
    tex_path: Optional[str]


class ReportDataBridge:
    """Centralized data extraction for the OsdagBridge report."""



    def __init__(self, backend, backend_results: dict, input_dict: dict, payload: "ReportPayload"):
        self.backend = backend
        self.backend_results = backend_results
        self.input_dict = input_dict
        self.payload = payload




    # =======================================================================
    # CHAPTER 4: ANALYSIS
    # =======================================================================

    def get_max_bm(self, load_case: str) -> str:
        """Extract max sagging BM for the given load case label. Used in: Chapter 4 (Analysis)."""
        try:
            if self.backend_results and "analysis" in self.backend_results:
                return f"{self.backend_results['analysis']['bmd'][load_case]['max']:.2f}"
            if hasattr(self.backend, "grillage_results"):
                pass
            if self.backend_results and "bmd_envelope" in self.backend_results:
                return f"{self.backend_results['bmd_envelope']['max_value']:.2f}"
        except Exception as exc:
            logger.warning(f"get_max_bm error: {exc}")
        return _ph(f"Max BM {load_case}")

    def get_max_sf(self, load_case: str) -> str:
        """Extract max shear force for the given load case label. Used in: Chapter 4 (Analysis)."""
        try:
            if self.backend_results and "analysis" in self.backend_results:
                return f"{self.backend_results['analysis']['sfd'][load_case]['max']:.2f}"
        except Exception as exc:
            logger.warning(f"get_max_sf error: {exc}")
        return _ph(f"Max SF {load_case}")

    def get_bm_location(self, load_case: str) -> str:
        """Extract X-location of max BM. Used in: Chapter 4 (Analysis)."""
        try:
            if self.backend_results and "analysis" in self.backend_results:
                return f"{self.backend_results['analysis']['bmd'][load_case]['x_max']:.2f}"
        except Exception as exc:
            logger.warning(f"get_bm_location error: {exc}")
        return _ph(f"Loc {load_case}")

    def get_sf_location(self, load_case: str) -> str:
        """Extract X-location of max SF. Used in: Chapter 4 (Analysis)."""
        try:
            if self.backend_results and "analysis" in self.backend_results:
                return f"{self.backend_results['analysis']['sfd'][load_case]['x_max']:.2f}"
        except Exception as exc:
            logger.warning(f"get_sf_location error: {exc}")
        return _ph(f"Loc SF {load_case}")

    def get_reaction(self, support: Literal["left", "right"], load_case: str) -> str:
        """Extract reaction at given support for the load case. Used in: Chapter 4 (Analysis)."""
        try:
            if self.backend_results and "reactions" in self.backend_results:
                return f"{self.backend_results['reactions'][load_case][support]:.2f}"
        except Exception as exc:
            logger.warning(f"get_reaction error: {exc}")
        return _ph(f"Reaction {support} {load_case}")

    def get_deflection(self, kind: Literal["ll", "total"]) -> str:
        """Extract maximum deflection. Used in: Chapter 4 (Analysis)."""
        try:
            if self.backend_results and "deflections" in self.backend_results:
                return f"{self.backend_results['deflections'][kind]['max']:.2f}"
        except Exception as exc:
            logger.warning(f"get_deflection error: {exc}")
        return _ph(f"Deflection {kind}")

    def get_deflection_limit(self, kind: Literal["ll", "total"], span_m: float) -> str:
        """Compute deflection limit (L/800 for ll, L/600 for total). Used in: Chapter 4 (Analysis)."""
        try:
            limit = (span_m * 1000) / 800 if kind == "ll" else (span_m * 1000) / 600
            return f"{limit:.2f}"
        except Exception as exc:
            logger.warning(f"get_deflection_limit error: {exc}")
        return _ph(f"Limit {kind}")

    def get_deflection_status(self, kind: Literal["ll", "total"], span_m: float) -> str:
        """Return PASS/FAIL status based on deflection limit. Used in: Chapter 4 (Analysis)."""
        try:
            if self.backend_results and "deflections" in self.backend_results:
                v = float(self.backend_results["deflections"][kind]["max"])
                limit = (span_m * 1000) / 800 if kind == "ll" else (span_m * 1000) / 600
                if v <= limit:
                    return r"\textcolor{black}{PASS}"
                return r"\textcolor{red}{FAIL}"
        except Exception as exc:
            logger.warning(f"get_deflection_status error: {exc}")
        return _ph(f"Status {kind}")

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
        return dist or state or 'Unknown Location'
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

def build_report_payload(request, input_dict, backend_results, backend):
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

        inp = input_dict

        # Inject detailed project location and weather data into inp dict
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
                
                if 'latitude' not in inp and lat_val:
                    inp['latitude'] = lat_val
                if 'longitude' not in inp and lon_val:
                    inp['longitude'] = lon_val
                    
                if 'seismic_zone' not in inp and weather.get('zone'):
                    inp['seismic_zone'] = weather.get('zone')
                if 'wind_speed' not in inp and weather.get('wind_speed'):
                    inp['wind_speed'] = weather.get('wind_speed')
                if 'shade_temp_max' not in inp and weather.get('max_temp'):
                    inp['shade_temp_max'] = weather.get('max_temp')
                if 'shade_temp_min' not in inp and weather.get('min_temp'):
                    inp['shade_temp_min'] = weather.get('min_temp')
        except Exception as e:
            logger.warning(f"Failed to parse project location data: {e}")

        asum = {}
        try:
            if backend_results:
                asum = backend_results.get('analysis_summary', {})
                for k, v in asum.items():
                    if k not in inp or not inp[k]:
                        inp[k] = v
                
                if 'overall_design_status' in backend_results:
                    inp['overall_design_status'] = backend_results['overall_design_status']
                if 'overall_utilization_ratio' in backend_results:
                    inp['max_ur'] = backend_results['overall_utilization_ratio']
                if 'governing_check' in backend_results:
                    inp['governing_check'] = backend_results['governing_check']
                
                if 'design_parameters' in backend_results:
                    for k, v in backend_results['design_parameters'].items():
                        if k not in inp or not inp[k]:
                            inp[k] = v
        except Exception:
            pass

        # Fallback: extract missing data directly from PlateGirderBridge if available
        if backend and backend.__class__.__name__ == 'PlateGirderBridge':
            try:
                # Sizing Result
                if hasattr(backend, 'sizing_result') and backend.sizing_result:
                    sr = backend.sizing_result
                    if 'num_girders' not in inp or not inp['num_girders']:
                        inp['num_girders'] = sr.no_of_girders
                    if 'girder_spacing' not in inp or not inp['girder_spacing']:
                        inp['girder_spacing'] = f"{sr.girder_spacing * 1e3:.0f} mm"
                    if 'deck_overhang' not in inp or not inp['deck_overhang']:
                        inp['deck_overhang'] = f"{sr.deck_overhang * 1e3:.0f} mm"
                
                if hasattr(backend, 'section_props') and backend.section_props and 'section_designation' not in inp:
                    sp = backend.section_props
                    D_mm     = sp.get('D', 0) * 1e3
                    tw_mm    = sp.get('t_w', 0) * 1e3
                    Bft_mm   = sp.get('B_top', 0) * 1e3
                    Tft_mm   = sp.get('t_f_top', 0) * 1e3
                    Bfb_mm   = sp.get('B_bot', sp.get('B_top', 0)) * 1e3
                    Tfb_mm   = sp.get('t_f_bot', sp.get('t_f_top', 0)) * 1e3
                    inp['section_designation'] = (
                        f"PG {D_mm:.0f}x{tw_mm:.0f}"
                        f" + {Bft_mm:.0f}x{Tft_mm:.0f}"
                        f" + {Bfb_mm:.0f}x{Tfb_mm:.0f}"
                    )

                # Deck thickness
                if hasattr(backend, 'additional_inputs') and ('deck_thickness' not in inp or not inp['deck_thickness']):
                    from osdagbridge.core.bridge_types.plate_girder.initial_sizing import DEFAULT_DECK_THICKNESS as _DEFAULT_DECK_THICKNESS_MM
                    from osdagbridge.core.bridge_components.super_structure.deck.geometry import deck_thickness_from_inputs
                    deck_t_m = deck_thickness_from_inputs(backend.additional_inputs, _DEFAULT_DECK_THICKNESS_MM)
                    inp['deck_thickness'] = f"{deck_t_m * 1e3:.0f} mm"
                
                # Lanes
                if hasattr(backend, 'basic_inputs') and ('num_lanes' not in inp or not inp['num_lanes']):
                    from osdagbridge.core.utils.common import KEY_CARRIAGEWAY_WIDTH
                    from osdagbridge.core.bridge_types.plate_girder.defaults import DEFAULT_CARRIAGEWAY_WIDTH_M
                    from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017
                    cw = backend.basic_inputs.get(KEY_CARRIAGEWAY_WIDTH, DEFAULT_CARRIAGEWAY_WIDTH_M)
                    try:
                        inp['num_lanes'] = IRC6_2017.table_6(float(cw))
                    except Exception:
                        pass
                
                # DCR checks
                if hasattr(backend, '_frontend') and backend._frontend:
                    from osdagbridge.core.utils.common import (
                        KEY_UTIL_FLEXURE, KEY_UTIL_SHEAR, KEY_UTIL_INTERACTION,
                        KEY_UTIL_LTB, KEY_UTIL_DEFLECTION_CRACK, KEY_UTIL_FATIGUE,
                        KEY_UTIL_LONG_TRANS_SHEAR, KEY_UTIL_STRESS_LIMITATION
                    )
                    frontend = backend._frontend
                    
                    name_map = {
                        KEY_UTIL_FLEXURE: "Flexure",
                        KEY_UTIL_SHEAR: "Shear",
                        KEY_UTIL_INTERACTION: "Flexure/Shear Interaction",
                        KEY_UTIL_LTB: "Lateral Torsional Buckling",
                        KEY_UTIL_DEFLECTION_CRACK: "Deflection / Crack Control",
                        KEY_UTIL_FATIGUE: "Fatigue",
                        KEY_UTIL_LONG_TRANS_SHEAR: "Transverse Shear",
                        KEY_UTIL_STRESS_LIMITATION: "Stress Limitation",
                    }
                    
                    max_ur_percent = -1
                    gov_key = ""
                    for key in name_map.keys():
                        val = frontend.get_output_value(key)
                        if val is not None:
                            try:
                                v = float(val)
                                if v > max_ur_percent:
                                    max_ur_percent = v
                                    gov_key = key
                            except Exception:
                                pass
                    
                    if max_ur_percent >= 0 and ('max_ur' not in inp or not inp['max_ur']):
                        inp['max_ur'] = f"{(max_ur_percent / 100.0):.3f}"
                        inp['overall_design_status'] = "FAIL" if max_ur_percent > 100 else "PASS"
                        inp['governing_check'] = name_map.get(gov_key, gov_key)
            except Exception as e:
                logger.warning("Error extracting data from PlateGirderBridge for report: %s", e)

        dc = []
        try:
            if backend and hasattr(backend, 'get_design_checks'):
                dc = backend.get_design_checks()
        except Exception:
            pass

        le = []
        try:
            if backend and hasattr(backend, 'get_design_log'):
                le = backend.get_design_log()
        except Exception:
            pass

        return ReportPayload(metadata=md, options=request.options, inputs=inp,
                             analysis_summary=asum, design_checks=dc,
                             figures=ReportFigures(), log_entries=le,
                             backend=backend, backend_results=backend_results or {})

    except Exception as exc:
        logger.warning("build_report_payload error: %s", exc)
        return ReportPayload(
            metadata=request.metadata, options=request.options,
            inputs={}, analysis_summary={}, design_checks=[],
            figures=ReportFigures(), log_entries=[],
            backend=None, backend_results={})


# ---------------------------------------------------------------------------
# Figure export helper (unchanged)
# ---------------------------------------------------------------------------

def export_grillage_figure(backend, output_dir, file_stem):
    try:
        ad = os.path.join(output_dir, f"{file_stem}_assets")
        os.makedirs(ad, exist_ok=True)
        op = os.path.join(ad, "grillage.png")
        if hasattr(backend, 'get_grillage_figure'):
            img = backend.get_grillage_figure()
            if hasattr(img, 'save'):
                img.save(op)
            elif isinstance(img, bytes):
                with open(op, 'wb') as fh:
                    fh.write(img)
            if os.path.exists(op):
                return os.path.abspath(op)
    except Exception as exc:
        logger.warning("grillage export: %s", exc)
    return None


# ===========================================================================
# Public entry point
# ===========================================================================

_FIGURE_MAP = [
    ('plan',                  'plan.png'),
    ('cross_section',         'cross_section.png'),
    ('final_geometry',        'final_geometry.png'),
    ('grillage',              'grillage.png'),
    ('longitudinal_elevation','longitudinal_elevation.png'),
    ('girder_3d',             'girder_3d.png'),
    ('girder_top',            'girder_top.png'),
    ('girder_end',            'girder_end.png'),
    ('bm_envelope',           'bm_envelope.png'),
    ('sf_envelope',           'sf_envelope.png'),
    ('shear_connector',       'shear_connector.png'),
    ('cross_bracing',         'cross_bracing.png'),
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
        assets_dir = os.path.join(request.output_dir, 'assets')
        os.makedirs(assets_dir, exist_ok=True)

        osdag_logo_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'Osdag Logo.png')
        iit_logo_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'IIT Bombay Logo.png')

        osdag_logo_latex = None
        if os.path.exists(osdag_logo_src):
            osdag_dest = os.path.join(assets_dir, 'osdag_logo.png')
            shutil.copy2(osdag_logo_src, osdag_dest)
            osdag_logo_latex = 'assets/osdag_logo.png'

        org_logo_latex = None
        if payload.metadata.logo_path and os.path.exists(payload.metadata.logo_path):
            org_dest = os.path.join(assets_dir, 'org_logo.png')
            shutil.copy2(payload.metadata.logo_path, org_dest)
            org_logo_latex = 'assets/org_logo.png'
        elif os.path.exists(iit_logo_src):
            org_dest = os.path.join(assets_dir, 'org_logo.png')
            shutil.copy2(iit_logo_src, org_dest)
            org_logo_latex = 'assets/org_logo.png'

        fig_paths = {}      # absolute paths — helpers do exists() check then convert to relative
        fig_rel   = {}      # 'assets/fname' relative paths for LaTeX embedding
        for attr, fname in _FIGURE_MAP:
            src = getattr(payload.figures, attr, None)
            if src and os.path.exists(src):
                dest = os.path.join(assets_dir, fname)
                shutil.copy2(src, dest)
                fig_paths[attr] = dest            # absolute, for os.path.exists()
                fig_rel[attr]   = 'assets/' + fname  # relative, for LaTeX

        # Assemble LaTeX document
        doc_parts = []
        doc_parts.append(preamble(payload.metadata.project_name, payload.metadata.job_number, payload.metadata.report_date, payload.metadata.subtitle or 'Rev 0'))
        doc_parts.append(title_page(payload.metadata, osdag_logo_latex, org_logo_latex))
        
        if payload.options.include_toc:
            doc_parts.append(toc_section())
            
        # Instantiate ReportDataBridge
        bridge = ReportDataBridge(payload.backend, payload.backend_results, payload.inputs, payload)
        span_m = float(payload.inputs.get(KEY_SPAN, 0) or 0)
        
        doc_parts.append(executive_summary(payload.inputs, fig_rel))
        doc_parts.append(ch1_project_info(payload.metadata))
        
        secs = payload.options.sections
        if 'Input Parameters' in secs:
            doc_parts.append(ch2_input_parameters(payload.metadata, payload.inputs))
            
        doc_parts.append(ch3_loads(payload.inputs))
        doc_parts.append(ch4_analysis(payload.analysis_summary, fig_rel, bridge, span_m))
        
        if 'Design Checks' in secs:
            doc_parts.append(ch5_design_checks(payload.design_checks, bridge))
            
        if payload.options.include_figures:
            doc_parts.append(ch6_drawings(fig_rel))
            
        doc_parts.append(ch7_quantities(payload.inputs))
        
        if 'Design Log' in secs:
            doc_parts.append(ch8_design_log(payload.log_entries))
            
        doc_parts.append(ch9_references())
        doc_parts.append(r"\end{document}")

        full_tex = "\n".join(doc_parts)
        
        pdf_path = os.path.join(request.output_dir, request.file_stem + '.pdf')
        tex_path = os.path.join(request.output_dir, request.file_stem + '.tex')

        # Write to temp dir first, compile there, then copy back
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_tex = os.path.join(tmp_dir, request.file_stem + '.tex')
            tmp_pdf = os.path.join(tmp_dir, request.file_stem + '.pdf')
            
            with open(tmp_tex, 'w', encoding='utf-8') as f:
                f.write(full_tex)
                
            # Mirror assets so LaTeX can find them
            tmp_assets = os.path.join(tmp_dir, 'assets')
            if os.path.exists(assets_dir):
                shutil.copytree(assets_dir, tmp_assets, dirs_exist_ok=True)
                
            # Compile twice for TOC and references
            for _ in range(2):
                try:
                    res = subprocess.run(
                        [compiler, '-interaction=nonstopmode', request.file_stem + '.tex'],
                        cwd=tmp_dir,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        check=False
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