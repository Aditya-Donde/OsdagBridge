from typing import List

from osdagbridge.core.utils.common import (
    KEY_DESIGN_MODE
)


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
    return _ch8_assumptions(is_custom)


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

\vspace{0.5cm}

\begingroup
\setlength{\tabcolsep}{3.5pt}
\begin{table}[H]
\caption{\textbf{IRC Codes}}
\begin{tabular}{|c|c|p{13cm}|}
\hline
\textbf{Code} & \textbf{Year} & \textbf{Title / Scope} \\ 
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

\begingroup
\setlength{\tabcolsep}{3.5pt}
\begin{table}[H]
\caption{\textbf{IS Codes}}
\begin{tabular}{|c|c|p{13cm}|}
\hline
\textbf{Code} & \textbf{Year} & \textbf{Scope} \\
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


