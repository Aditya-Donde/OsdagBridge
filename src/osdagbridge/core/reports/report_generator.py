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

import os, shutil, logging, datetime, tempfile, subprocess
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Literal

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
\usepackage{tocloft}
\usepackage{setspace}
\usepackage{enumitem}
\usepackage{caption}
\usepackage{subcaption}
\usepackage{multirow}
\usepackage{colortbl}
\usepackage{longtable}
\usepackage{titlesec}
\usepackage{lastpage}

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

\title{}
\author{}
\date{}

\begin{document}
"""


# ═══════════════════════════════════════════════════════════════════════════════
# TITLE PAGE
# ═══════════════════════════════════════════════════════════════════════════════

def title_page(m, logo_path):
    import os
    # logo_path here is the path AS SEEN by pdflatex in its working directory.
    # We always use a forward-slash relative path so it is portable across OS.
    if logo_path:
        logo = r'\includegraphics[width=0.6\textwidth]{' + logo_path.replace('\\', '/') + r'}\\[1cm]'
    else:
        logo = r'\textit{(Logo not available)}\\[1cm]'

    return r"""
\begin{titlepage}
\thispagestyle{firstpage}
\centering
\vspace*{1.5cm}
""" + logo + r"""
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
\renewcommand{\cftdot}{}
\renewcommand{\cftchapleader}{\hfill}
\renewcommand{\cftsecleader}{\hfill}
\renewcommand{\cftsubsecleader}{\hfill}
\renewcommand{\cftchappresnum}{}
\renewcommand{\cftchapaftersnum}{}
\renewcommand{\cftchapnumwidth}{1.5em}
\renewcommand{\cftchapfont}{\normalfont}
\renewcommand{\cftchappagefont}{\normalfont}
\renewcommand{\cftbeforechapskip}{2pt}

\newpage
\setlength{\cftbeforetoctitleskip}{0pt}
\setlength{\cftaftertoctitleskip}{30pt}
\renewcommand{\contentsname}{\centering\Large\bfseries Table of Contents}
\tableofcontents
"""


# ═══════════════════════════════════════════════════════════════════════════════
# EXECUTIVE SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════

def executive_summary(inp, fig_paths, bridge: "ReportDataBridge") -> str:
    plan_fig = _fig_or_placeholder(fig_paths.get('plan'), 'Figure 1 -- Overall Bridge Plan')
    cs_fig = _fig_or_placeholder(fig_paths.get('cross_section'),
                                  'Figure 2 -- Typical Cross-Section (with girder, deck, barriers, footpath)')
    geom_fig = _fig_or_placeholder(fig_paths.get('final_geometry'),
                                    'Figure 3 -- 3D View of Bridge Superstructure')

    g1 = bridge.get_girder_summary("Girder 1")
    g2 = bridge.get_girder_summary("Girder 2")
    g3 = bridge.get_girder_summary("Girder 3")
    g4 = bridge.get_girder_summary("Girder 4")
    g5a = bridge.get_girder_summary("Girder 5A")
    g5b = bridge.get_girder_summary("Girder 5B")

    sections = f"Section Designation & {g1['section']} & {g2['section']} & {g3['section']} & {g4['section']} & {g5a['section']} & {g5b['section']} \\\\"
    gov_checks = f"Governing Check & {g1['governing_check']} & {g2['governing_check']} & {g3['governing_check']} & {g4['governing_check']} & {g5a['governing_check']} & {g5b['governing_check']} \\\\"
    urs = f"Utilization Ratio & {g1['max_ur']} & {g2['max_ur']} & {g3['max_ur']} & {g4['max_ur']} & {g5a['max_ur']} & {g5b['max_ur']} \\\\"

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
\textbf{Span} & """ + (_v(inp, 'span', ' m') or _ph('Span Length')) + r""" m \\
\hline
\textbf{Carriageway Width} & """ + (_v(inp, 'carriageway_width', ' m') or _ph('Carriageway Width')) + r""" \\
\hline
\textbf{No. of Traffic Lanes} & """ + (_v(inp, 'num_lanes') or _ph('No. of Lanes')) + r""" \\
\hline
\textbf{No. of Girders} & """ + (_v(inp, 'num_girders') or _ph('No. of Girders')) + r""" \\
\hline
\textbf{Girder Spacing} & """ + (_v(inp, 'girder_spacing') or _ph('Girder Spacing')) + r""" \\
\hline
\textbf{Deck Thickness} & """ + (_v(inp, 'deck_thickness') or _ph('Deck Thickness')) + r""" \\
\hline
\textbf{Overall Design Status} & PASS / FAIL \\
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
\rowcolor[HTML]{91B014}
\textcolor{white}{\textbf{}} &
\textcolor{white}{\textbf{Girder 1}} &
\textcolor{white}{\textbf{Girder 2}} &
\textcolor{white}{\textbf{Girder 3}} &
\textcolor{white}{\textbf{Girder 4}} &
\multicolumn{2}{c|}{\textcolor{white}{\textbf{Girder 5}}} \\
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
\noindent{\small \textbf{Note:} \textit{Utilization ratio (UR) = demand / capacity. A value $< 1.0$ indicates a passing check.}}

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

\noindent{\color{olive}\textbf{Note:} \textit{These inputs are mandatory and were provided by the user.}}

\subsection*{Project Location}
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

\subsection*{Bridge Geometry}
\label{subsec:bridge-geometry}

\begin{table}[H]
\vspace{-6pt}
\begin{tabular}{|L{5.5cm}|L{8.5cm}|}
\hline
\textbf{Type of Structure} & Highway Bridge \\
\hline
\textbf{Span (m)} & """ + (_v(inp,'span',' m') or _ph('L') + ' m') + r""" \\
\hline
\textbf{Carriageway Width (m)} & """ + (_v(inp,'carriageway_width',' m') or _ph('CW') + ' m') + r""" \\
\hline
\textbf{Include Median} & """ + (_v(inp,'include_median') or 'Yes / No') + r""" \\
\hline
\textbf{Footpath} & """ + (_v(inp,'footpath') or 'None / Single / Both') + r""" \\
\hline
\textbf{Skew Angle (degrees)} & """ + (_v(inp,'skew_angle','°') or _ph('Angle') + '°') + r""" (IRC 24 Cl. 504.8 limit: $\pm$15°) \\
\hline
\end{tabular}
\end{table}

\subsection*{Material Selection}
\label{subsec:material}

\begin{table}[H]
\vspace{-6pt}
\begin{tabular}{|L{5.5cm}|L{8.5cm}|}
\hline
\textbf{Girder Steel Grade (IS 2062)} & """ + (_v(inp,'girder_steel_grade') or _ph('e.g. E 350')) + r""" \\
\hline
\textbf{Cross Bracing Steel Grade} & """ + (_v(inp,'cross_bracing_grade') or _ph('e.g. E 350')) + r""" \\
\hline
\textbf{End Diaphragm Steel Grade} & """ + (_v(inp,'end_diaphragm_grade') or _ph('e.g. E 350')) + r""" \\
\hline
\textbf{Concrete Deck Grade (IRC 22)} & """ + (_v(inp,'deck_concrete_grade') or _ph('e.g. M 40')) + r""" \\
\hline
\end{tabular}
\end{table}

\newpage
\section{Additional Inputs}
\label{sec:additional-inputs}

Where the user has modified additional inputs, those values are reported here. Where no modification was made, the software default is shown.

\noindent\textit{\textbf{Table 2.1 Typical Section Details}}

\begin{table}[H]
\vspace{-6pt}
\begin{tabularx}{\textwidth}{|L{5.5cm}|X|}
\hline
\textbf{Overall Bridge Width (m)} & """ + (_v(inp,'overall_bridge_width') or _ph('Calculated')) + r""" \\[6pt]
\hline
\textbf{No. of Girders} & """ + (_v(inp,'num_girders') or _ph('n')) + r""" [SOFTWARE DEFAULT / USER] \\[6pt]
\hline
\textbf{Girder Spacing (m)} & """ + (_v(inp,'girder_spacing',' m') or _ph('s') + ' m') + r""" [SOFTWARE DEFAULT: 2.5 m] \\[6pt]
\hline
\textbf{Deck Overhang Width (m)} & """ + (_v(inp,'deck_overhang',' m') or _ph(r'd\_oh') + ' m') + r""" [SOFTWARE DEFAULT: 0.35 x spacing] \\[6pt]
\hline
\textbf{Deck Thickness (mm)} & """ + (_v(inp,'deck_thickness',' mm') or _ph('dt') + ' mm') + r""" [SOFTWARE DEFAULT: 200 mm] \\[6pt]
\hline
\textbf{Footpath Width (m)} & """ + (_v(inp,'footpath_width',' m') or _ph('$f_w$') + ' m') + r""" (IRC 5 Cl. 104.3.6 min: 1.5 m) \\[6pt]
\hline
\textbf{No. of Traffic Lanes} & """ + (_v(inp,'num_lanes') or _ph(r'n\_lanes')) + r""" (per IRC 5 Cl. 104.3.1) \\[6pt]
\hline
\end{tabularx}
\end{table}

\vspace{0.8em}
\noindent\textit{\textbf{Table 2.2 Components Details}}

\begin{table}[H]
\vspace{-6pt}
\begin{tabularx}{\textwidth}{|L{5.5cm}|X|}
\hline
\textbf{Crash Barrier Type} & """ + (_v(inp,'crash_barrier_type') or _ph('IRC 5 RCC / Metallic / Custom')) + r""" \\[6pt]
\hline
\textbf{Crash Barrier Load (kN/m)} & """ + (_v(inp,'crash_barrier_load') or _ph('Load')) + r""" \\[6pt]
\hline
\textbf{Median Type} & """ + (_v(inp,'median_type') or _ph('IRC 5 Raised Kerb / N/A')) + r""" \\[6pt]
\hline
\textbf{Railing Type} & """ + (_v(inp,'railing_type') or _ph('IRC 5 RCC / Steel / N/A')) + r""" \\[6pt]
\hline
\textbf{Railing Load (kN/m)} & 1.5 kN/m [SOFTWARE DEFAULT per IRC 6 Cl. 206.5] \\[6pt]
\hline
\textbf{Wearing Course Material} & """ + (_v(inp,'wearing_course_material') or _ph('Bituminous / Concrete')) + r""" \\[6pt]
\hline
\textbf{Wearing Course Thickness (mm)} & """ + (_v(inp,'wearing_course_thickness',' mm') or _ph(r'wc\_t') + ' mm') + r""" [SOFTWARE DEFAULT: 80 mm] \\[6pt]
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
\noindent\textit{\textbf{Table 2.3 Member Properties: Girder Details}}

\vspace{0.4em}
\noindent
\begin{table}[H]
\captionsetup{justification=raggedright,singlelinecheck=false}
\caption*{\textit{\textbf{Table 2.3(a) Girder General Information}}}
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
\caption*{\textit{\textbf{Table 2.3(b) Girder Section Dimensions}}}
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
\caption*{\textit{\textbf{Table 2.3(c) Girder Restraint and Stiffener Details}}}
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
\noindent\textit{\textbf{Table 2.4 Member Properties: Cross Bracing Details}}

\vspace{0.4em}
\noindent
\setlength{\tabcolsep}{4pt}
\begin{longtable}{|p{2.8cm}|p{2.8cm}|p{1.9cm}|p{1.9cm}|p{1.9cm}|p{1.9cm}|}
\hline
\multicolumn{2}{|l|}{} &
\textbf{Between Girders 1 and 2} &
\textbf{Between Girders 2 and 3} &
\textbf{Between Girders 3 and 4} &
\textbf{Between Girders 4 and 5} \\
\hline
\textbf{Member IDs} & & B1M1 -- B1M10 & B2M1 -- B2M10 & B3M1 -- B3M10 & B4M1 -- B4M10 \\[6pt]
\hline
\textbf{Type of Bracing} & K-Bracing / X-Bracing [SOFTWARE DEFAULT based on D/S] & & & & \\[10pt]
\hline
\textbf{Bracing Section} & \placeholder{e.g. ISA 100x100x8} [SOFTWARE DEFAULT] & & & & \\[10pt]
\hline
\textbf{Cross Bracing Spacing (m)} & \placeholder{$s_{br}$} m [SOFTWARE DEFAULT: 3.5 m] & & & & \\[10pt]
\hline
\textbf{No. of Cross Bracing Panels} & \placeholder{$n_{br}$} & & & & \\[10pt]
\hline
\end{longtable}

\noindent\textit{\textbf{Table 2.5 Member Properties: End Diaphragm Details}}

\vspace{0.4em}
\noindent
\setlength{\tabcolsep}{4pt}
\begin{longtable}{|p{2.8cm}|p{2.8cm}|p{1.9cm}|p{1.9cm}|p{1.9cm}|p{1.9cm}|}
\hline
\multicolumn{2}{|l|}{} &
\textbf{Between Girders 1 and 2} &
\textbf{Between Girders 2 and 3} &
\textbf{Between Girders 3 and 4} &
\textbf{Between Girders 4 and 5} \\
\hline
\textbf{Member IDs} & & E1M1, E1M2 & E2M1, E2M2 & E3M1, E3M2 & E4M1, E4M2 \\[6pt]
\hline
\textbf{Type of Bracing} & K-Bracing / X-Bracing [SOFTWARE DEFAULT based on D/S] & & & & \\[10pt]
\hline
\textbf{Bracing Section} & \placeholder{e.g. ISA 100x100x8} [SOFTWARE DEFAULT] & & & & \\[10pt]
\hline
\textbf{Cross Bracing Spacing (m)} & \placeholder{$s_{br}$} m [SOFTWARE DEFAULT: 3.5 m] & & & & \\[10pt]
\hline
\textbf{No. of Cross Bracing Panels} & \placeholder{$n_{br}$} & & & & \\[10pt]
\hline
\end{longtable}
"""


def _shear_connector_table(inp):
    return r"""
\subsection*{Shear Connectors}
\label{subsec:shear-connectors}

\noindent\textit{\textbf{Table 2.6 Shear Connector Details}}

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
\subsection*{Partial Safety Factors}
\label{subsec:safety-factors}

\noindent\textit{\textbf{Table 2.7 Partial Safety Factors}}

\vspace{0.3em}
\noindent{\color{olive}\textbf{Note:} \textit{All values are per IRC 22 Table 1 unless user-modified.}}

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


def ch3_loads(inp, bridge: "ReportDataBridge"):
    return r"""
\chapter{Loads and Load Combinations}

This section summarizes all loads applied to the bridge and the load combinations considered for analysis and design.

\vspace{1em}
\noindent\textit{\textbf{Table 3.1 Dead Load -- Self Weight}}

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
\noindent\textit{\textbf{Table 3.2 Dead Load for Surfacing (DW)}}

\begin{table}[H]
\vspace{-6pt}
\begin{tabularx}{\textwidth}{|L{5.5cm}|X|}
\hline
\textbf{Wearing Course Load} & """ + (_v(inp,'wearing_course_material') or _ph('Density')) + r""" x """ + (_v(inp,'wearing_course_thickness') or _ph('Thickness')) + r""" \\[6pt]
\hline
\textbf{Additional SIDL (Crash Barrier)} & """ + (_v(inp,'crash_barrier_load') or _ph('Load')) + r""" kN/m per barrier \\[6pt]
\hline
\textbf{Railing Load} & 1.5 kN/m per railing [IRC 6 Cl. 206.5] \\[6pt]
\hline
\end{tabularx}
\end{table}

\vspace{1em}
\noindent\textit{\textbf{Table 3.3 Live Loads (LL)}}

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
\noindent\textit{\textbf{Table 3.4 Wind Load (WL) --- per IRC 6}}

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
\textbf{Hourly Mean Wind Speed, Vz} & """ + bridge.get_wind_value("Vz") + r""" m/s \\[6pt]
\hline
\textbf{Hourly Wind Pressure, Pz} & """ + bridge.get_wind_value("Pz") + r""" N/m\textsuperscript{2} \\[6pt]
\hline
\textbf{Transverse Wind Force} & """ + bridge.get_wind_value("Fw_T") + r""" kN \\[6pt]
\hline
\textbf{Longitudinal Wind Force} & """ + bridge.get_wind_value("Fw_L") + r""" kN \\[6pt]
\hline
\textbf{Vertical Wind Force} & """ + bridge.get_wind_value("Fw_V") + r""" kN \\[6pt]
\hline
\end{tabularx}
\end{table}

\vspace{1em}
\noindent\textit{\textbf{Table 3.5 Earthquake Load (EL) --- per IRC 6}}

\begin{table}[H]
\vspace{-6pt}
\begin{tabularx}{\textwidth}{|L{5.5cm}|X|}
\hline
\textbf{Seismic Zone} & """ + (_v(inp,'seismic_zone') or _ph('Zone')) + r""" [from Project Location] \\[6pt]
\hline
\textbf{Zone Factor, Z} & """ + bridge.get_seismic_value("Z") + r""" \\[6pt]
\hline
\textbf{Importance Factor, I} & """ + (_v(inp, "importance_factor") or "1.0 [SOFTWARE DEFAULT]") + r""" \\[6pt]
\hline
\textbf{Type of Soil} & """ + (_v(inp, "soil_type") or "Type I -- Rocky [SOFTWARE DEFAULT]") + r""" \\[6pt]
\hline
\textbf{Sa/g} & """ + bridge.get_seismic_value("Sa_g") + r""" \\[6pt]
\hline
\textbf{Horizontal Seismic Coefficient, Ah} & """ + bridge.get_seismic_value("Ah") + r""" \\[6pt]
\hline
\textbf{Vertical Seismic Coefficient, Av} & """ + bridge.get_seismic_value("Av") + r""" = 2/3 $\times$ Ah \\[6pt]
\hline
\textbf{Horizontal Seismic Force} & """ + bridge.get_seismic_value("Feq_L") + r""" kN (longitudinal), """ + bridge.get_seismic_value("Feq_T") + r""" kN (transverse) \\[6pt]
\hline
\end{tabularx}
\end{table}

\vspace{1em}
\noindent\textit{\textbf{Table 3.6 Temperature Load (EL) --- per IRC 6}}

\begin{table}[H]
\vspace{-6pt}
\begin{tabularx}{\textwidth}{|L{5.5cm}|X|}
\hline
\textbf{Maximum Shade Temperature} & """ + (_v(inp,'shade_temp_max') or _ph(r'T\_max')) + r""" $^\circ$C \\[6pt]
\hline
\textbf{Minimum Shade Temperature} & """ + (_v(inp,'shade_temp_min') or _ph('$T_{min}$')) + r""" $^\circ$C \\[6pt]
\hline
\textbf{Effective Bridge Temp. Range} & """ + bridge.get_temperature_value("T_eff_min") + r""" to """ + bridge.get_temperature_value("T_eff_max") + r""" $^\circ$C \\[6pt]
\hline
\textbf{Temperature Rise / Fall for Design} & +""" + bridge.get_temperature_value("dT_rise") + r""" $^\circ$C / -""" + bridge.get_temperature_value("dT_fall") + r""" $^\circ$C \\[6pt]
\hline
\end{tabularx}
\end{table}

\vspace{1em}
\noindent\textit{\textbf{Table 3.7 Load Combinations}}

\vspace{0.4em}
The following load combinations were evaluated per IRC 6. The governing combination for each member is identified in the design checks section.

\begin{table}[H]
\vspace{-6pt}
\begin{tabularx}{\textwidth}{|C{3.2cm}|C{3.5cm}|C{4.5cm}|>{\centering\arraybackslash}X|}
\hline
\rowcolor[HTML]{91B014}
\textcolor{white}{\textbf{Combination ID}} & \textcolor{white}{\textbf{Description}} & \textcolor{white}{\textbf{Load Cases}} & \textcolor{white}{\textbf{Governs For}} \\[6pt]
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

\noindent{\color{olive}\textbf{Note:}} \textit{All IRC 6 load combinations are auto-generated by OsdagBridge. User-defined custom combinations, if any, are appended.}
"""


def ch4_analysis(asum, fig_paths, bridge: "ReportDataBridge", span_m: float):
    return r"""
\chapter{Analysis Results}

A grillage model was used for structural analysis. The deck is idealized as a grid of elastic beam elements --- longitudinal members represent the composite steel girders with effective slab, and transverse members represent the slab or cross frames. This section summarizes the critical output from that analysis.

\vspace{1em}
\noindent\textit{\textbf{Table 4.1 Summary of Maximum Demands}}

\begin{table}[H]
\vspace{-6pt}
\begin{tabularx}{\textwidth}{|>{\centering\arraybackslash}X|>{\centering\arraybackslash}C{2.8cm}|>{\centering\arraybackslash}C{2.2cm}|>{\centering\arraybackslash}C{2.5cm}|>{\centering\arraybackslash}C{2.2cm}|>{\centering\arraybackslash}C{1.8cm}|}
\hline
\rowcolor[HTML]{91B014}
\textcolor{white}{\textbf{Load Case}} & \textcolor{white}{\textbf{Max BM (kN-m)}} & \textcolor{white}{\textbf{Location (m)}} & \textcolor{white}{\textbf{Max SF (kN)}} & \textcolor{white}{\textbf{Location (m)}} & \textcolor{white}{\textbf{Girder}} \\[6pt]
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
\noindent\textit{\textbf{Table 4.2 Reactions at Supports}}

\begin{table}[H]
\vspace{-6pt}
\begin{tabularx}{\textwidth}{|>{\centering\arraybackslash}X|>{\centering\arraybackslash}X|>{\centering\arraybackslash}X|}
\hline
\rowcolor[HTML]{91B014}
\textcolor{white}{\textbf{Load Case}} & \textcolor{white}{\textbf{Left Support (kN)}} & \textcolor{white}{\textbf{Right Support (kN)}} \\[6pt]
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
\noindent\textit{\textbf{Table 4.3 Deflection Summary (Live Load \& Total Load)}}

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
    # Generate Girder rows
    girder_rows = []
    for girder_id in ["Girder 1", "Girder 2", "Girder 3", "Girder 4", "Girder 5A", "Girder 5B"]:
        checks = [
            ("Flexure Check (Max Sagging)", "Flexure Check (Max Sagging)"),
            ("Shear Check (Max Shear)", "Shear Check (Max Shear)"),
            ("Flexure-Shear Interaction", "Flexure-Shear Interaction"),
            ("Lateral Torsional Buckling (Construction Stage)", "Lateral Torsional Buckling (Construction Stage)"),
            ("Fatigue Assessment (IS 800)", "Fatigue Assessment (IS 800)")
        ]
        girder_rows.append(f"\\multirow{{5}}{{*}}{{{girder_id}}}")
        for i, (label, check_key) in enumerate(checks):
            c = bridge.get_girder_check(girder_id, check_key)
            row = f" & {label} & {c['demand']} & {c['capacity']} & {c['ur']} & {c['status_tex']} \\\\"
            if i == 0:
                girder_rows.append(row)
            else:
                girder_rows.append(f"\\cline{{2-6}}\n{row}")
        girder_rows.append("\\hline")
    girder_tex = "\n".join(girder_rows)

    # Generate Bracing rows
    bracing_rows = []
    # Collect all unique member_ids from bracing checks data
    sources = []
    if hasattr(bridge.backend, "get_bracing_checks"):
        sources = bridge.backend.get_bracing_checks() or []
    elif bridge.backend_results.get("bracing_checks"):
        sources = bridge.backend_results["bracing_checks"]
    br_member_ids = list(dict.fromkeys(
        c.get("member_id", "") for c in sources if c.get("member_id")
    ))
    if not br_member_ids:
        br_member_ids = ["B1M1", "E1M1"]  # safe fallback

    for br_id in br_member_ids:
        all_checks_for_member = [c for c in sources if c.get("member_id") == br_id]
        check_count = len(all_checks_for_member) if all_checks_for_member else 3
        
        # If we have actual checks, use their names. Otherwise fallback.
        if all_checks_for_member:
            checks = [(c.get("check", "Unknown Check"), c.get("check", "Unknown Check")) for c in all_checks_for_member]
        else:
            checks = [
                ("Axial Tension", "Axial Tension"),
                ("Axial Compression", "Axial Compression"),
                ("Slenderness Check (KL/r)", "Slenderness Check (KL/r)")
            ]
        
        bracing_rows.append(f"\\multirow{{{check_count}}}{{*}}{{{br_id}}}")
        for i, (label, check_key) in enumerate(checks):
            c = bridge.get_bracing_check(br_id, check_key)
            row = f" & {label} & {c['demand']} & {c['capacity']} & {c['ur']} & {c['status_tex']} \\\\"
            if i == 0:
                bracing_rows.append(row)
            else:
                bracing_rows.append(f"\\cline{{2-6}}\n{row}")
        bracing_rows.append("\\hline")
    bracing_tex = "\n".join(bracing_rows)

    # Generate Shear Connector rows
    sc_rows = []
    for label, check_key in [
        ("Ultimate Shear Capacity per Stud ($P_{u}$)", "Ultimate Shear Capacity per Stud"),
        ("Longitudinal Shear per Unit Length ($V_L$)", "Longitudinal Shear per Unit Length"),
        ("Stud Spacing (Min/Max limits)", "Stud Spacing")
    ]:
        c = bridge.get_shear_connector_check(check_key)
        sc_rows.append(f"{label} & {c['demand']} & {c['capacity']} & {c['ur']} & {c['status_tex']} \\\\\n\\hline")
    sc_tex = "\n".join(sc_rows)

    # Generate Deck Slab rows
    deck_rows = []
    for label, check_key in [
        ("Flexure (Sagging Moment)", "Flexure (Sagging Moment)"),
        ("Flexure (Hogging Moment over supports)", "Flexure (Hogging Moment over supports)"),
        ("Shear Check", "Shear Check")
    ]:
        c = bridge.get_deck_check(check_key)
        deck_rows.append(f"{label} & {c['demand']} & {c['capacity']} & {c['ur']} & {c['status_tex']} \\\\\n\\hline")
    deck_tex = "\n".join(deck_rows)

    return r"""
\chapter{Design Checks}

This section summarizes all critical design checks performed on the bridge components. The governing load combination and resultant utilization ratios (Demand / Capacity) are presented.

\section{Girder Checks}
\label{sec:girder-checks}

\noindent\textit{\textbf{Table 5.1 Main Girder Design Checks}}

\vspace{0.4em}
\noindent
\begin{longtable}{|C{1.8cm}|p{6cm}|C{2cm}|C{2cm}|C{2cm}|C{2cm}|}
\hline
\rowcolor[HTML]{91B014}
\textcolor{white}{\textbf{Girder}} & \textcolor{white}{\textbf{Check Description}} & \textcolor{white}{\textbf{Demand}} & \textcolor{white}{\textbf{Capacity}} & \textcolor{white}{\textbf{Utilization Ratio}} & \textcolor{white}{\textbf{Status}} \\
\hline
\endfirsthead

\hline
\rowcolor[HTML]{91B014}
\textcolor{white}{\textbf{Girder}} & \textcolor{white}{\textbf{Check Description}} & \textcolor{white}{\textbf{Demand}} & \textcolor{white}{\textbf{Capacity}} & \textcolor{white}{\textbf{Utilization Ratio}} & \textcolor{white}{\textbf{Status}} \\
\hline
\endhead

""" + girder_tex + r"""
\end{longtable}

\section{Cross Bracing Checks}
\label{sec:bracing-checks}

\noindent\textit{\textbf{Table 5.2 Cross Bracing Design Checks}}

\vspace{0.4em}
\noindent
\begin{longtable}{|C{1.8cm}|p{6cm}|C{2cm}|C{2cm}|C{2cm}|C{2cm}|}
\hline
\rowcolor[HTML]{91B014}
\textcolor{white}{\textbf{Bracing}} & \textcolor{white}{\textbf{Check Description}} & \textcolor{white}{\textbf{Demand}} & \textcolor{white}{\textbf{Capacity}} & \textcolor{white}{\textbf{Utilization Ratio}} & \textcolor{white}{\textbf{Status}} \\
\hline
\endfirsthead

\hline
\rowcolor[HTML]{91B014}
\textcolor{white}{\textbf{Bracing}} & \textcolor{white}{\textbf{Check Description}} & \textcolor{white}{\textbf{Demand}} & \textcolor{white}{\textbf{Capacity}} & \textcolor{white}{\textbf{Utilization Ratio}} & \textcolor{white}{\textbf{Status}} \\
\hline
\endhead

""" + bracing_tex + r"""
\end{longtable}

\section{Shear Connector Checks}
\label{sec:shear-connector-checks}

\noindent\textit{\textbf{Table 5.3 Shear Connector Verification}}

\vspace{0.4em}
\noindent
\begin{table}[H]
\begin{tabular}{|p{6.5cm}|C{2.5cm}|C{2.5cm}|C{1.5cm}|C{1.5cm}|}
\hline
\rowcolor[HTML]{91B014}
\textcolor{white}{\textbf{Check Description}} & \textcolor{white}{\textbf{Demand}} & \textcolor{white}{\textbf{Capacity}} & \textcolor{white}{\textbf{Ratio}} & \textcolor{white}{\textbf{Status}} \\
\hline
""" + sc_tex + r"""
\end{tabular}
\end{table}

\section{Deck Slab Checks}
\label{sec:deck-checks}

\noindent\textit{\textbf{Table 5.4 RC Deck Slab Verification (IRC 112)}}

\vspace{0.4em}
\noindent
\begin{table}[H]
\begin{tabular}{|p{6.5cm}|C{2.5cm}|C{2.5cm}|C{1.5cm}|C{1.5cm}|}
\hline
\rowcolor[HTML]{91B014}
\textcolor{white}{\textbf{Check Description}} & \textcolor{white}{\textbf{Demand}} & \textcolor{white}{\textbf{Capacity}} & \textcolor{white}{\textbf{Ratio}} & \textcolor{white}{\textbf{Status}} \\
\hline
""" + deck_tex + r"""
\end{tabular}
\end{table}
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

{\color{osdagGreen}\subsection{Typical Cross Section}}
\label{subsec:cross-section}

"""
            + cs + r"""

\vspace{1em}

{\color{osdagGreen}\subsection{Longitudinal Elevation}}
\label{subsec:elevation}

"""
            + elev + r"""

\vspace{1em}

\section{Plate Girder --- Detailed Views}
\label{sec:girder-views}

{\color{osdagGreen}\subsection{3D View of Single Plate Girder}}
\label{subsec:3d-girder}

"""
            + g3d + r"""

\vspace{1em}

{\color{osdagGreen}\subsection{Top View of Girder}}
\label{subsec:top-view}

"""
            + gtop + r"""

\vspace{1em}

{\color{osdagGreen}\subsection{Front and Side Views (End Panel Detail)}}
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


def ch7_quantities(bridge: "ReportDataBridge"):
    return r"""
\chapter{Material Take-Off / Bill of Quantities}
\label{ch:boq}

This section provides a preliminary estimate of material quantities based on the final designed geometry.

\begin{table}[H]
\begin{tabularx}{\textwidth}{|>{\centering\arraybackslash}C{1cm}|X|>{\centering\arraybackslash}C{2cm}|>{\centering\arraybackslash}C{2cm}|>{\centering\arraybackslash}C{2cm}|}
\hline
\rowcolor[HTML]{91B014}
\textcolor{white}{\textbf{S.N.}} & \textcolor{white}{\textbf{Item Description}} & \textcolor{white}{\textbf{Unit}} & \textcolor{white}{\textbf{Quantity}} & \textcolor{white}{\textbf{Remarks}} \\
\hline
1 & Structural Steel (IS 2062) for Girders & MT & """ + bridge.get_quantity("steel_girders_mt") + r""" & \\
\hline
2 & Structural Steel for Cross Bracings & MT & """ + bridge.get_quantity("steel_bracing_mt") + r""" & \\
\hline
3 & Concrete (M40) for Deck Slab & Cu.m & """ + bridge.get_quantity("concrete_deck_cum") + r""" & \\
\hline
4 & Reinforcement Steel (Fe 500) & MT & """ + bridge.get_quantity("rebar_deck_mt") + r""" & \\
\hline
5 & Shear Stud Connectors & Nos & """ + bridge.get_quantity("shear_studs_nos") + r""" & \\
\hline
\end{tabularx}
\end{table}
"""


def ch8_design_log(log_entries: List[str]) -> str:
    lines_tex = []
    if not log_entries:
        lines_tex.append(r"\textit{No design log entries recorded.}")
    else:
        for entry in log_entries:
            for line in entry.split('\n'):
                line_clean = line.strip()
                if not line_clean:
                    continue
                # Escape LaTeX special characters if needed, but for simplicity we assume log messages are mostly safe
                # Or just simple replace:
                line_escaped = line_clean.replace('_', r'\_').replace('%', r'\%')
                
                if "WARNING" in line_escaped.upper():
                    lines_tex.append(rf"\textcolor{{blue}}{{{line_escaped}}}\\")
                elif "INFO" in line_escaped.upper():
                    lines_tex.append(rf"\textcolor{{osdagGreen}}{{{line_escaped}}}\\")
                elif "ERROR" in line_escaped.upper():
                    lines_tex.append(rf"\textcolor{{red}}{{{line_escaped}}}\\")
                else:
                    continue

        if not lines_tex:
            lines_tex.append(r"\textit{No design log entries recorded.}")

    logs_str = "\n".join(lines_tex)

    return r"""
\chapter{Software Design Log}
\label{ch:design-log}

The following is an excerpt of the system logs generated during the execution of the design module. This includes warnings, optimization loops, and iteration counts.

\vspace{1em}
\begin{flushleft}
""" + logs_str + r"""
\end{flushleft}
"""


def ch9_references():
    return r"""
\chapter{References}
\label{ch:references}

\begin{enumerate}
    \item Indian Roads Congress (2015). \textit{IRC:5-2015 Standard Specifications and Code of Practice for Road Bridges, Section I - General Features of Design}.
    \item Indian Roads Congress (2017). \textit{IRC:6-2017 Standard Specifications and Code of Practice for Road Bridges, Section II - Loads and Load Combinations}.
    \item Indian Roads Congress (2015). \textit{IRC:22-2015 Standard Specifications and Code of Practice for Road Bridges, Section VI - Composite Construction (Limit State Design)}.
    \item Indian Roads Congress (2010). \textit{IRC:24-2010 Standard Specifications and Code of Practice for Road Bridges, Steel Road Bridges (Limit State Method)}.
    \item Indian Roads Congress (2011). \textit{IRC:112-2011 Code of Practice for Concrete Road Bridges}.
    \item Bureau of Indian Standards (2007). \textit{IS 800:2007 General Construction in Steel - Code of Practice}.
\end{enumerate}
"""

# --- TEMPLATES END ---


# ---------------------------------------------------------------------------
# Public data-classes (API unchanged)
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

    _QUANTITY_ALIASES = {
        "steel_girders_mt":  ["steel_girders_mt", "girder_steel_mt", "steel_girder", "girder_steel"],
        "steel_bracing_mt":  ["steel_bracing_mt", "bracing_steel_mt", "steel_bracing", "bracing_steel"],
        "concrete_deck_cum": ["concrete_deck_cum", "concrete_m3", "deck_concrete_cum", "concrete_deck"],
        "rebar_deck_mt":     ["rebar_deck_mt", "rebar_mt", "reinforcement_mt", "rebar"],
        "shear_studs_nos":   ["shear_studs_nos", "stud_count", "num_studs", "shear_studs"],
    }

    def __init__(self, backend, backend_results: dict, input_dict: dict, payload: "ReportPayload"):
        self.backend = backend
        self.backend_results = backend_results
        self.input_dict = input_dict
        self.payload = payload

    def get_max_bm(self, load_case: str) -> str:
        """Extract max sagging BM for the given load case label."""
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
        """Extract max shear force for the given load case label."""
        try:
            if self.backend_results and "analysis" in self.backend_results:
                return f"{self.backend_results['analysis']['sfd'][load_case]['max']:.2f}"
        except Exception as exc:
            logger.warning(f"get_max_sf error: {exc}")
        return _ph(f"Max SF {load_case}")

    def get_bm_location(self, load_case: str) -> str:
        """Extract X-location of max BM."""
        try:
            if self.backend_results and "analysis" in self.backend_results:
                return f"{self.backend_results['analysis']['bmd'][load_case]['x_max']:.2f}"
        except Exception as exc:
            logger.warning(f"get_bm_location error: {exc}")
        return _ph(f"Loc {load_case}")

    def get_sf_location(self, load_case: str) -> str:
        """Extract X-location of max SF."""
        try:
            if self.backend_results and "analysis" in self.backend_results:
                return f"{self.backend_results['analysis']['sfd'][load_case]['x_max']:.2f}"
        except Exception as exc:
            logger.warning(f"get_sf_location error: {exc}")
        return _ph(f"Loc SF {load_case}")

    def get_reaction(self, support: Literal["left", "right"], load_case: str) -> str:
        """Extract reaction at given support for the load case."""
        try:
            if self.backend_results and "reactions" in self.backend_results:
                return f"{self.backend_results['reactions'][load_case][support]:.2f}"
        except Exception as exc:
            logger.warning(f"get_reaction error: {exc}")
        return _ph(f"Reaction {support} {load_case}")

    def get_deflection(self, kind: Literal["ll", "total"]) -> str:
        """Extract maximum deflection."""
        try:
            if self.backend_results and "deflections" in self.backend_results:
                return f"{self.backend_results['deflections'][kind]['max']:.2f}"
        except Exception as exc:
            logger.warning(f"get_deflection error: {exc}")
        return _ph(f"Deflection {kind}")

    def get_deflection_limit(self, kind: Literal["ll", "total"], span_m: float) -> str:
        """Compute deflection limit (L/800 for ll, L/600 for total)."""
        try:
            limit = (span_m * 1000) / 800 if kind == "ll" else (span_m * 1000) / 600
            return f"{limit:.2f}"
        except Exception as exc:
            logger.warning(f"get_deflection_limit error: {exc}")
        return _ph(f"Limit {kind}")

    def get_deflection_status(self, kind: Literal["ll", "total"], span_m: float) -> str:
        """Return PASS/FAIL status based on deflection limit."""
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

    def get_girder_check(self, girder_id: str, check_name: str) -> dict:
        """Return specific design check dictionary for a girder."""
        try:
            sources = self.payload.design_checks or []
            if not sources and hasattr(self.backend, "get_design_checks"):
                sources = self.backend.get_design_checks() or []
            for c in sources:
                if isinstance(c, dict) and c.get("girder_id") == girder_id and c.get("check") == check_name:
                    ur = float(c.get("utilisation_ratio", 0.0))
                    st = str(c.get("status", "FAIL")).upper()
                    st_tex = r"\textcolor{osdagGreen}{\textbf{PASS}}" if st == "PASS" else r"\textcolor{red}{\textbf{FAIL}}"
                    return {"demand": _tex(c.get("demand", "")), "capacity": _tex(c.get("capacity", "")), "ur": f"{ur:.3f}", "status_tex": st_tex}
        except Exception as exc:
            logger.warning(f"get_girder_check error: {exc}")
        return {"demand": _ph("demand"), "capacity": _ph("capacity"), "ur": _ph("ur"), "status_tex": _ph("status")}

    def get_all_girder_checks(self, girder_id: str) -> list[dict]:
        """Return all design checks for a given girder."""
        try:
            res = []
            sources = self.payload.design_checks or []
            if not sources and hasattr(self.backend, "get_design_checks"):
                sources = self.backend.get_design_checks() or []
            for c in sources:
                if isinstance(c, dict) and c.get("girder_id") == girder_id:
                    ur = float(c.get("utilisation_ratio", 0.0))
                    st = str(c.get("status", "FAIL")).upper()
                    st_tex = r"\textcolor{osdagGreen}{\textbf{PASS}}" if st == "PASS" else r"\textcolor{red}{\textbf{FAIL}}"
                    res.append({"check": _tex(c.get("check", "")), "demand": _tex(c.get("demand", "")), "capacity": _tex(c.get("capacity", "")), "ur": f"{ur:.3f}", "status_tex": st_tex})
            if res:
                return res
        except Exception as exc:
            logger.warning(f"get_all_girder_checks error: {exc}")
        return []

    def get_girder_summary(self, girder_id: str) -> dict:
        """Return governing check name, UR, and section designation for a girder.
        
        Returns dict with keys: 'section', 'governing_check', 'max_ur'.
        Falls back to _ph() for any missing value.
        """
        try:
            sources = self.payload.design_checks or []
            if not sources and hasattr(self.backend, "get_design_checks"):
                sources = self.backend.get_design_checks() or []
            girder_checks = [c for c in sources if isinstance(c, dict) and c.get("girder_id") == girder_id]
            if girder_checks:
                governing = max(girder_checks, key=lambda c: float(c.get("utilisation_ratio", 0.0)))
                ur = float(governing.get("utilisation_ratio", 0.0))
                return {
                    "section":         _tex(governing.get("section_designation", self.input_dict.get("section_designation", ""))),
                    "governing_check": _tex(governing.get("check", "")),
                    "max_ur":          f"{ur:.3f}",
                }
        except Exception as exc:
            logger.warning(f"get_girder_summary error: {exc}")
        return {"section": _ph("Section"), "governing_check": _ph("Check"), "max_ur": _ph("UR")}

    def get_bracing_check(self, member_id: str, check_name: str) -> dict:
        """Return bracing design check dictionary."""
        try:
            checks = []
            if hasattr(self.backend, "get_bracing_checks"):
                checks = self.backend.get_bracing_checks() or []
            elif self.backend_results and "bracing_checks" in self.backend_results:
                checks = self.backend_results["bracing_checks"] or []
            for c in checks:
                if isinstance(c, dict) and c.get("member_id") == member_id and c.get("check") == check_name:
                    ur = float(c.get("utilisation_ratio", 0.0))
                    st = str(c.get("status", "FAIL")).upper()
                    st_tex = r"\textcolor{osdagGreen}{\textbf{PASS}}" if st == "PASS" else r"\textcolor{red}{\textbf{FAIL}}"
                    return {"demand": _tex(c.get("demand", "")), "capacity": _tex(c.get("capacity", "")), "ur": f"{ur:.3f}", "status_tex": st_tex}
        except Exception as exc:
            logger.warning(f"get_bracing_check error: {exc}")
        return {"demand": _ph("demand"), "capacity": _ph("capacity"), "ur": _ph("ur"), "status_tex": _ph("status")}

    def get_shear_connector_check(self, check_name: str) -> dict:
        """Return shear connector design check dictionary."""
        try:
            checks = []
            if hasattr(self.backend, "get_shear_connector_checks"):
                checks = self.backend.get_shear_connector_checks()
            elif self.backend_results and "shear_connector_checks" in self.backend_results:
                checks = self.backend_results["shear_connector_checks"]
            for c in checks:
                if isinstance(c, dict) and c.get("check") == check_name:
                    ur = float(c.get("utilisation_ratio", 0.0))
                    st = str(c.get("status", "FAIL")).upper()
                    st_tex = r"\textcolor{osdagGreen}{\textbf{PASS}}" if st == "PASS" else r"\textcolor{red}{\textbf{FAIL}}"
                    return {"demand": _tex(c.get("demand", "")), "capacity": _tex(c.get("capacity", "")), "ur": f"{ur:.3f}", "status_tex": st_tex}
        except Exception as exc:
            logger.warning(f"get_shear_connector_check error: {exc}")
        return {"demand": _ph("demand"), "capacity": _ph("capacity"), "ur": _ph("ur"), "status_tex": _ph("status")}

    def get_deck_check(self, check_name: str) -> dict:
        """Return deck slab design check dictionary."""
        try:
            checks = []
            if hasattr(self.backend, "get_deck_checks"):
                checks = self.backend.get_deck_checks()
            elif self.backend_results and "deck_checks" in self.backend_results:
                checks = self.backend_results["deck_checks"]
            for c in checks:
                if isinstance(c, dict) and c.get("check") == check_name:
                    ur = float(c.get("utilisation_ratio", 0.0))
                    st = str(c.get("status", "FAIL")).upper()
                    st_tex = r"\textcolor{osdagGreen}{\textbf{PASS}}" if st == "PASS" else r"\textcolor{red}{\textbf{FAIL}}"
                    return {"demand": _tex(c.get("demand", "")), "capacity": _tex(c.get("capacity", "")), "ur": f"{ur:.3f}", "status_tex": st_tex}
        except Exception as exc:
            logger.warning(f"get_deck_check error: {exc}")
        return {"demand": _ph("demand"), "capacity": _ph("capacity"), "ur": _ph("ur"), "status_tex": _ph("status")}

    def get_quantity(self, item_key: str) -> str:
        """Return material quantity."""
        try:
            aliases = self._QUANTITY_ALIASES.get(item_key, [item_key])
            takeoff_dict = {}
            if hasattr(self.backend, "get_material_takeoff"):
                takeoff_dict = self.backend.get_material_takeoff() or {}
            
            # Try aliases
            for alias in aliases:
                # 1. Try backend material takeoff
                if alias in takeoff_dict:
                    val = takeoff_dict[alias]
                    return f"{int(val)}" if isinstance(val, int) or "nos" in alias or "count" in alias else f"{float(val):.2f}"
                
                # 2. Try input dict
                if alias in self.input_dict:
                    val = self.input_dict[alias]
                    try:
                        return f"{int(float(val))}" if "nos" in alias or "count" in alias else f"{float(val):.2f}"
                    except (ValueError, TypeError):
                        return str(val)
                
                # 3. Try backend_results quantities
                if self.backend_results and "quantities" in self.backend_results:
                    if alias in self.backend_results["quantities"]:
                        val = self.backend_results["quantities"][alias]
                        return f"{int(val)}" if isinstance(val, int) or "nos" in alias or "count" in alias else f"{float(val):.2f}"
        except Exception as exc:
            logger.warning(f"get_quantity error: {exc}")
        return _ph(item_key)

    def get_wind_value(self, key: str) -> str:
        """Return computed wind value."""
        try:
            if self.backend_results and "wind" in self.backend_results:
                if key in self.backend_results["wind"]:
                    return str(self.backend_results["wind"][key])
            if hasattr(self.backend, "wind_results"):
                if key in self.backend.wind_results:
                    return str(self.backend.wind_results[key])
        except Exception as exc:
            logger.warning(f"get_wind_value error: {exc}")
        return _ph(key)

    def get_seismic_value(self, key: str) -> str:
        """Return computed seismic value."""
        try:
            if self.backend_results and "seismic" in self.backend_results:
                if key in self.backend_results["seismic"]:
                    return str(self.backend_results["seismic"][key])
            if hasattr(self.backend, "seismic_results"):
                if key in self.backend.seismic_results:
                    return str(self.backend.seismic_results[key])
        except Exception as exc:
            logger.warning(f"get_seismic_value error: {exc}")
        return _ph(key)

    def get_temperature_value(self, key: str) -> str:
        """Return computed temperature value."""
        try:
            if self.backend_results and "temperature" in self.backend_results:
                if key in self.backend_results["temperature"]:
                    return str(self.backend_results["temperature"][key])
            if hasattr(self.backend, "temperature_results"):
                if key in self.backend.temperature_results:
                    return str(self.backend.temperature_results[key])
        except Exception as exc:
            logger.warning(f"get_temperature_value error: {exc}")
        return _ph(key)



# ---------------------------------------------------------------------------
# Public builder helper (unchanged signature)
# ---------------------------------------------------------------------------

def build_report_payload(request, input_dict, backend_results, backend):
    try:
        rd  = request.metadata.report_date or datetime.date.today().isoformat()
        lp  = request.metadata.logo_path
        if not lp:
            lp = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "assets", "Osdag Logo.png")
        pl  = request.metadata.project_location or input_dict.get('project_location', '')

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

        _all_keys = [
            'span', 'carriageway_width', 'skew_angle', 'bridge_type', 'material',
            'dead_load', 'live_load', 'seismic_zone', 'wind_speed', 'girder_spacing',
            'num_girders', 'deck_thickness', 'num_lanes', 'girder_steel_grade',
            'deck_concrete_grade', 'governing_check', 'max_ur', 'latitude', 'longitude',
            'include_median', 'footpath', 'overall_design_status',
            'deck_overhang', 'footpath_width', 'crash_barrier_type',
            'crash_barrier_load', 'median_type', 'railing_type', 'railing_load',
            'wearing_course_material', 'wearing_course_thickness',
            'stud_diameter', 'stud_height', 'stud_fy', 'stud_fu', 'num_studs',
            'shade_temp_max', 'shade_temp_min',
            'cross_bracing_grade', 'end_diaphragm_grade',
            'gamma_m0', 'gamma_m1', 'gamma_c', 'gamma_s', 'gamma_v',
            'gamma_fft', 'gamma_mft', 'impact_factor', 'braking_load',
            'footpath_live_load', 'terrain_type', 'avg_exposed_height',
            'soil_type', 'importance_factor',
        ]
        inp = {k: input_dict.get(k, '') for k in _all_keys}

        asum = {}
        try:
            if backend_results:
                asum = backend_results.get('analysis_summary', {})
        except Exception:
            pass

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
# pdflatex auto-discovery
# ===========================================================================

def _find_pdflatex():
    import sys
    if shutil.which('pdflatex'):
        return 'pdflatex'
    candidates = []
    if sys.platform == 'win32':
        local = os.environ.get('LOCALAPPDATA', '')
        home  = os.path.expanduser('~')
        candidates = [
            os.path.join(local, 'Programs', 'MiKTeX', 'miktex', 'bin', 'x64'),
            os.path.join(home, 'AppData', 'Local', 'Programs', 'MiKTeX', 'miktex', 'bin', 'x64'),
            r'C:\Program Files\MiKTeX\miktex\bin\x64',
            r'C:\Program Files (x86)\MiKTeX\miktex\bin\x64',
            r'C:\texlive\2024\bin\windows',
            r'C:\texlive\2025\bin\windows',
        ]
    for d in candidates:
        exe = (os.path.join(d, 'pdflatex.exe')
               if sys.platform == 'win32'
               else os.path.join(d, 'pdflatex'))
        if os.path.isfile(exe):
            os.environ['PATH'] = d + os.pathsep + os.environ.get('PATH', '')
            logger.info("Found pdflatex at: %s", exe)
            return exe
    return 'pdflatex'


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
        compiler = _find_pdflatex()
        logger.info("Compiler: %s", compiler)

        os.makedirs(request.output_dir, exist_ok=True)
        assets_dir = os.path.join(request.output_dir, 'assets')
        os.makedirs(assets_dir, exist_ok=True)

        logo_dest = None          # absolute path on disk (for copying)
        logo_latex = None         # path string embedded in LaTeX (relative to tmp_dir)
        if payload.metadata.logo_path and os.path.exists(payload.metadata.logo_path):
            logo_dest = os.path.join(assets_dir, 'logo.png')
            shutil.copy2(payload.metadata.logo_path, logo_dest)
            logo_latex = 'assets/logo.png'   # relative — pdflatex runs in tmp_dir

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
        doc_parts.append(title_page(payload.metadata, logo_latex))
        
        if payload.options.include_toc:
            doc_parts.append(toc_section())
            
        # Instantiate ReportDataBridge
        bridge = ReportDataBridge(payload.backend, payload.backend_results, payload.inputs, payload)
        span_m = float(payload.inputs.get("span", 0) or 0)
        
        doc_parts.append(executive_summary(payload.inputs, fig_rel, bridge))
        doc_parts.append(ch1_project_info(payload.metadata))
        
        secs = payload.options.sections
        if 'Input Parameters' in secs:
            doc_parts.append(ch2_input_parameters(payload.metadata, payload.inputs))
            
        doc_parts.append(ch3_loads(payload.inputs, bridge))
        doc_parts.append(ch4_analysis(payload.analysis_summary, fig_rel, bridge, span_m))
        
        if 'Design Checks' in secs:
            doc_parts.append(ch5_design_checks(payload.design_checks, bridge))
            
        if payload.options.include_figures:
            doc_parts.append(ch6_drawings(fig_rel))
            
        doc_parts.append(ch7_quantities(bridge))
        
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
                    subprocess.run(
                        [compiler, '-interaction=nonstopmode', '--enable-installer', request.file_stem + '.tex'],
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
        return ReportResult(pdf_path=None, tex_path=tex_path)

    except Exception as exc:
        logger.error("generate_report failed: %s", exc, exc_info=True)
        if tex_path and os.path.exists(tex_path):
            return ReportResult(pdf_path=None, tex_path=tex_path)
        return ReportResult(pdf_path=None, tex_path=None)