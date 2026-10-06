from osdagbridge.core.reports.report_utils import render_report_table


def ch1_project_info(m):
    return r"""
\chapter{Project Information}

This section records all project metadata as entered by the designer.

\section{Project and Design Team Details}
\label{sec:project-details}

""" + render_report_table(
    "Project and Design Team Details",
    [["Project Name", m.project_name], ["Project Location", m.project_location],
     ["Designer", m.designer], ["Reviewer", m.reviewer], ["Organization", m.company],
     ["Client", m.client], ["Software Version", "OsdagBridge"]],
    widths=[5.5, 8.5]) + r"""


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


