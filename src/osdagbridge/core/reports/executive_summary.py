# =============================================================================
# EXECUTIVE SUMMARY
# =============================================================================

from osdagbridge.core.reports.report_utils import _fig_or_placeholder, _render_value, _tex, get_girder_entries, render_report_table
from osdagbridge.core.utils.common import (
    KEY_CARRIAGEWAY_WIDTH,
    KEY_SD_SECTION_DESIGNATION,
    KEY_SPAN,
    KEY_STRUCTURE_TYPE,
    KEY_TS_DECK_THICKNESS,
    KEY_TS_GIRDER_SPACING,
    KEY_TS_NO_OF_GIRDERS
)


def _max_float(values):
    """Return the largest value coercible to float, or None if there are none."""
    out = None
    for v in values:
        try:
            f = float(v)
        except (TypeError, ValueError):
            continue
        if out is None or f > out:
            out = f
    return out


def _max_member_efficiency(pair_designs):
    """Maximum Osdag 'efficiency' (utilization ratio) over a cross-bracing or
    end-diaphragm result dump (nested pair -> member -> force_type -> raw).
    Reads already-computed results only; nothing is recalculated here."""
    from osdagbridge.core.bridge_types.plate_girder.results_data import _extract_osdag_summary
    if not isinstance(pair_designs, dict):
        return None
    best = None
    for members in pair_designs.values():
        if not isinstance(members, dict):
            continue
        for force_types in members.values():
            if not isinstance(force_types, dict):
                continue
            for raw in force_types.values():
                try:
                    val = _extract_osdag_summary(raw or {}).get("efficiency")
                    if val is None:
                        continue
                    f = float(val)
                except (TypeError, ValueError, AttributeError):
                    continue
                if best is None or f > best:
                    best = f
    return best


def _deck_governing(deck_results):
    """Return (max_ur, label) for the deck slab's worst utilization, e.g.
    (0.72, "ULS - Bottom (Sagging)"). Returns (None, "") when none exist."""
    try:
        from osdagbridge.core.bridge_types.plate_girder.ui_fields_additional_input import (
            DECK_DESIGN_SUMMARY_SCHEMA,
        )
        labels = {c["key"]: c["label"]
                  for c in DECK_DESIGN_SUMMARY_SCHEMA.get("utilization_card", {}).get("checks", [])
                  if str(c.get("key", "")).startswith("ur_")}
    except Exception:
        labels = {}
    best_ur, best_key = None, ""
    for k, v in (deck_results or {}).items():
        if not str(k).startswith("ur_"):
            continue
        try:
            f = float(v)
        except (TypeError, ValueError):
            continue
        if best_ur is None or f > best_ur:
            best_ur, best_key = f, str(k)
    if best_ur is None:
        return (None, "")
    return (best_ur, labels.get(best_key, best_key))


def _governing_member(pair_designs):
    """Return (efficiency, label) for the worst member/force-type in a cross-bracing
    or end-diaphragm result dump, e.g. (0.63, "Diagonal (Compression)").
    Returns (None, "") when none exist."""
    from osdagbridge.core.bridge_types.plate_girder.results_data import _extract_osdag_summary
    if not isinstance(pair_designs, dict):
        return (None, "")
    best_ur, best_label = None, ""
    for members in pair_designs.values():
        if not isinstance(members, dict):
            continue
        for member_name, force_types in members.items():
            if not isinstance(force_types, dict):
                continue
            for force_type, raw in force_types.items():
                try:
                    val = _extract_osdag_summary(raw or {}).get("efficiency")
                    if val is None:
                        continue
                    f = float(val)
                except (TypeError, ValueError, AttributeError):
                    continue
                if best_ur is None or f > best_ur:
                    best_ur = f
                    best_label = f"{str(member_name).title()} ({str(force_type).title()})"
    return (best_ur, best_label)


def executive_summary(input_dict, output_dict, fig_paths) -> str:
    plan_fig = _fig_or_placeholder(fig_paths.get('girder_top'), 'Figure 1 -- Overall Bridge Plan')
    cs_fig = _fig_or_placeholder(fig_paths.get('cross_section'),
                                  'Figure 2 -- Typical Cross-Section (with girder, deck, barriers, footpath)')
    geom_fig = _fig_or_placeholder(fig_paths.get('final_geometry'),
                                    'Figure 3 -- 3D View of Bridge Superstructure')

    # All girders share the same section, governing check, and UR.
    # The section designation is produced by the designer pipeline, so it lives
    # in output_dict (not input_dict).
    sec = _render_value(output_dict, KEY_SD_SECTION_DESIGNATION)

    # Pull the stored result dicts once, then work off these locals.
    # No value is recomputed here; the pipeline already filled these in.
    design_results = output_dict.get("design_results", {}) or {}
    per_girder     = design_results.get("per_girder", {}) or {}
    deck_results   = output_dict.get("deck_design_results", {}) or {}
    cb_results     = output_dict.get("crossbracing_design_results", {}) or {}
    ed_results     = output_dict.get("end_diaphragm_design_results", {}) or {}

    # Overall Design Status: girder checks only; Pass if every check passes,
    # otherwise Fail with the names of the failing checks. Each check carries a
    # pre-computed {name, dcr, status}.
    failing = []                        # failing check names (order-preserving, deduped)
    gov_name, gov_dcr = "", None
    girder_max_ur = None
    for g, gd in per_girder.items():
        if str(g).startswith("EB"):     # skip edge-beam pseudo girders
            continue
        for chk in (gd.get("checks") or []):
            try:
                _val = chk.get("dcr")
                if _val is None:
                    dcr = None
                else:
                    dcr = float(_val)
            except (TypeError, ValueError):
                dcr = None
            name = str(chk.get("name", "")).strip()
            is_fail = ("FAIL" in str(chk.get("status", "")).upper()) or (dcr is not None and dcr > 1.0)
            if is_fail and name and name not in failing:
                failing.append(name)
            if dcr is not None:
                if gov_dcr is None or dcr > gov_dcr:
                    gov_dcr, gov_name = dcr, name
                if girder_max_ur is None or dcr > girder_max_ur:
                    girder_max_ur = dcr

    if not per_girder:
        overall_design_status = ""
    elif failing:
        overall_design_status = "Fail (" + ", ".join(failing) + ")"
    else:
        overall_design_status = "Pass"

    # Overall Utilization Ratio: maximum UR across all bridge components,
    # tagged with the governing component (e.g. "1.05 (Deck slab)").
    component_urs = []                  # (ur_value, component_label)
    if girder_max_ur is not None:
        component_urs.append((girder_max_ur, "Girder"))
    deck_max = _max_float([v for k, v in deck_results.items() if str(k).startswith("ur_")])
    if deck_max is not None:
        component_urs.append((deck_max, "Deck slab"))
    for results, label in ((cb_results, "Cross bracing"), (ed_results, "End diaphragm")):
        m = _max_member_efficiency(results)
        if m is not None:
            component_urs.append((m, label))
    if component_urs:
        max_ur, max_label = max(component_urs, key=lambda t: t[0])
        overall_utilization_ratio = f"{max_ur:.2f} ({max_label})"
    else:
        overall_utilization_ratio = ""

    gov_raw = str(gov_name).strip() if gov_name not in (None, '', 'None') else ''
    gov = _tex(gov_raw) if gov_raw else ''
    ur = _tex(overall_utilization_ratio) if overall_utilization_ratio else ''
    gov_table = (r"\makecell[c]{" + r"\\".join(_tex(p) for p in gov_raw.replace(".", ". ").replace(":", ": ").split()) + "}"
                 if gov_raw else '')

    # --- Dynamic Table 1: fetch backend-populated labels via exact suffix pattern ---
    # defaults.py populates: KEY_MP_GD_SELECT_GIRDER + '.G{i}' = 'G{i}'
    #                        KEY_MP_GD_MEMBER_ID     + '.G{i}.M1' = 'G{i}M1'
    labels = get_girder_entries(input_dict)
    if not labels:
        labels = [("", "")]
    n_cols = len(labels)

    # Column widths: row-label column fixed at 2.8cm; girder columns share remainder
    label_col_cm = 2.8
    # Available width is about 15.0cm for A4 with 1in margins; each girder col gets equal share
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
    table1 = render_report_table(
        "Final Bridge Geometry (after optimization)",
        [["Member ID"] + [mid for _, mid in labels],
         ["Section Designation"] + [sec] * n_cols,
         [r"Govern-\linebreak{}ing\linebreak{}Check"] + [gov_table] * n_cols,
         [r"Utiliza-\linebreak{}tion Ratio"] + [ur] * n_cols],
        headers=[""] + [lbl for lbl, _ in labels],
        widths=[1.6] + [1.25] * n_cols,
        align=["L"] + ["C"] * n_cols,
        escape=False)
    table1 = r"{\footnotesize" + "\n" + table1 + "\n}"

    # Key Design Outcomes rows: controlling check, its UR, and pass/fail per component.
    def _outcome_cells(component, check, ur, is_fail):
        chk_cell = _tex(check) if check else "---"
        if ur is None:
            ur_cell, status_cell = "---", "---"
        else:
            ur_cell = f"{ur:.2f}"
            status_cell = r"\textcolor{red}{Fail}" if is_fail else "Pass"
        return [component, chk_cell, ur_cell, status_cell]

    _cb_ur, _cb_check = _governing_member(cb_results)
    _ed_ur, _ed_check = _governing_member(ed_results)
    _dk_ur, _dk_check = _deck_governing(deck_results)

    overview_table = render_report_table(
        "Project Overview",
        [[r"\textbf{Bridge Type}", _render_value(input_dict, KEY_STRUCTURE_TYPE)],
         [r"\textbf{Design Standard}", "IRC 5, IRC 6, IRC 22, IRC 24, IS 800"],
         [r"\textbf{Span}", _render_value(input_dict, KEY_SPAN, ' m')],
         [r"\textbf{Carriageway Width}", _render_value(input_dict, KEY_CARRIAGEWAY_WIDTH, ' m')],
         [r"\textbf{No. of Girders}", _render_value(input_dict, KEY_TS_NO_OF_GIRDERS)],
         [r"\textbf{Girder Spacing}", _render_value(input_dict, KEY_TS_GIRDER_SPACING)],
         [r"\textbf{Deck Thickness}", _render_value(input_dict, KEY_TS_DECK_THICKNESS)],
         [r"\textbf{Overall Design Status}", _tex(overall_design_status)],
         [r"\textbf{Governing Check}", gov],
         [r"\textbf{Overall Utilization Ratio (max)}", ur]],
        widths=[5.5, 8.5], align=["L", "L"], escape=False)

    outcome_rows = [
        _outcome_cells("Girder Design", gov_name, girder_max_ur, bool(failing)) if per_girder
            else _outcome_cells("Girder Design", "", None, False),
        _outcome_cells("Cross Bracing Design", _cb_check, _cb_ur, _cb_ur is not None and _cb_ur > 1.0),
        _outcome_cells("End Diaphragm Design", _ed_check, _ed_ur, _ed_ur is not None and _ed_ur > 1.0),
        _outcome_cells("Deck Design", _dk_check, _dk_ur, _dk_ur is not None and _dk_ur > 1.0),
    ]
    outcome_table = render_report_table(
        "Design Outcome Summary", outcome_rows,
        headers=["component", "controlling check", "utilization ratio", "status"],
        widths=[4.0, 5.5, 2.8, 1.8], align=["L", "L", "C", "C"], escape=False)

    return r"""
\newpage
{\centering\Large\bfseries Executive Summary\par}
\addcontentsline{toc}{chapter}{Executive Summary}
\vspace{0.8em}
\setcounter{table}{0}
\renewcommand{\thetable}{E.\arabic{table}}

This section provides a concise summary of the bridge design, key inputs, governing loads, and final design outcomes.

\section*{Project Overview}
\addcontentsline{toc}{section}{Project Overview}
\label{sec:project-overview}

""" + overview_table + "\n\n" + plan_fig + r"""

\newpage

""" + cs_fig + '\n\n' + geom_fig + '\n\n' + table1 + r"""

\vspace{0.25em}\nopagebreak
\noindent\parbox{\linewidth}{\textit{Note: UR = demand / capacity; UR $< 1.0$ indicates a passing check.}}

\vspace{1em}

\section*{Key Design Outcomes Summary}
\addcontentsline{toc}{section}{Key Design Outcomes Summary}
\label{sec:key-outcomes}

""" + outcome_table + r"""

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
\renewcommand{\thetable}{\thechapter.\arabic{table}}
\titleformat{\chapter}[block]{\normalfont\Large\bfseries\centering}{\thechapter}{1em}{}
\titlespacing*{\chapter}{0pt}{-30pt}{10pt}
"""
