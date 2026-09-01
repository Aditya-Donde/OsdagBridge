import os
import re

import matplotlib
import matplotlib.pyplot as plt

from osdagbridge.core.utils.common import (
    KEY_MP_GD_MEMBER_ID,
    KEY_MP_GD_SELECT_GIRDER,
    KEY_TS_NO_OF_GIRDERS,
)

_GROUPED_TABLE_PROBE = False
_GROUPED_TABLE_BREAKS = set()


def configure_grouped_table_breaks(probe=False, breaks=None):
    global _GROUPED_TABLE_PROBE, _GROUPED_TABLE_BREAKS
    _GROUPED_TABLE_PROBE = probe
    _GROUPED_TABLE_BREAKS = set(breaks or [])


def grouped_table_key(caption):
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in str(caption)).strip("_")[:80]


def _tex(value):
    """Escape a Python value for safe LaTeX embedding."""
    s = str(value) if value is not None else ''
    if not s:
        return r''
    # Normalise non-ASCII glyphs from section designations (e.g. "∠ 100 ⅹ 100ⅹ 10")
    # that pdflatex cannot render.
    for uni, ascii_ in [('∠', 'L'), ('ⅹ', 'x'), ('×', 'x')]:
        s = s.replace(uni, ascii_)
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
    if isinstance(val, float):
        val = f"{val:.2f}".rstrip("0").rstrip(".")
    return _tex(val) + unit


def _table_layout(headers, rows, widths=None, align=None):
    """Column count, scaled column widths (cm) and alignment shared by the table renderers."""
    headers = headers or []
    ncols = max(1, len(headers) or max((len(row) for row in rows), default=1))
    max_content_width = 15.5 - (0.43 * ncols) - (0.02 * (ncols + 1))
    if widths is None:
        def _score(cell):
            text = str(cell or "").replace("\\allowbreak{}", "")
            for ch in "\\{}$_^":
                text = text.replace(ch, "")
            longest = max((len(part) for part in text.split()), default=0)
            return max(1.0, min(18.0, longest * 0.65 + len(text) * 0.12))
        widths = [
            max(_score(headers[i] if i < len(headers) else ""),
                max((_score(row[i]) for row in rows if i < len(row)), default=1.0))
            for i in range(ncols)
        ]
        min_width = min(2.0, max(1.2, max_content_width / ncols * 0.65))
        remaining = max_content_width - (min_width * ncols)
        widths = ([min_width + remaining * w / sum(widths) for w in widths]
                  if remaining > 0 and sum(widths) > 0 else [max_content_width / ncols] * ncols)
    else:
        widths = list(widths)
        if len(widths) < ncols:
            widths.extend([widths[-1] if widths else round(14.0 / ncols, 2)] * (ncols - len(widths)))
        widths = widths[:ncols]
    scale = max_content_width / sum(widths) if sum(widths) > 0 else 1
    widths = [round(w * scale, 2) for w in widths]
    
    return ncols, widths, align or ["L"] * ncols


def render_report_table(caption, rows, headers=None, widths=None, align=None, longtable=False, escape=True, header_rows=None, header_clines=None, body_latex=None):
    headers = headers or []
    ncols, widths, align = _table_layout(headers, rows, widths, align)

    def _header(cell):
        text = str(cell or "")
        text = text[:1].upper() + text[1:] if text else text
        return r"\textbf{" + (_tex(text) if escape else text) + "}"
    colspec = "|" + "|".join(f"{a}{{{w}cm}}" for a, w in zip(align, widths)) + "|"
    header = ""
    if header_rows:
        rendered = []
        header_clines = header_clines or {}
        for row_idx, row in enumerate(header_rows):
            cells = []
            for cell in row:
                if isinstance(cell, tuple):
                    text, span = cell
                    cells.append(r"\multicolumn{" + str(span) + r"}{c|}{\textbf{" + (_tex(text) if escape else text) + "}}")
                else:
                    cells.append(_header(cell) if cell else "")
            rendered.append(" & ".join(cells) + r" \\")
            if row_idx in header_clines:
                rendered.append(r"\cline{" + header_clines[row_idx] + "}")
        header = "\\hline\n" + "\n".join(rendered) + "\n\\hline\n"
    elif headers:
        header_row = " & ".join(_header(h) for h in headers) + r" \\"
        header = "\\hline\n" + header_row + "\n\\hline\n"
    fmt = _tex if escape else str
    body = body_latex if body_latex is not None else "\n".join(" & ".join(fmt(cell) for cell in row) + r" \\" + "\n\\hline" for row in rows)

    if longtable:
        repeat = (header + "\\endfirsthead\n" + header + "\\endhead\n") if header else "\\hline\n"
        return ("\\begin{longtable}{" + colspec + "}\n"
                + "\\captionsetup{justification=centering,font={small,it}}\n\\caption{"
                + _tex(caption) + "}\\\\\n" + repeat + body
                + "\n\\end{longtable}")

    return ("\\begin{table}[H]\n\\centering\n\\captionsetup{justification=centering,font={small,it}}\n\\caption{"
            + _tex(caption) + "}\n\\begin{tabular}{" + colspec
            + "}\n" + (header or "\\hline\n") + body
            + "\n\\end{tabular}\n\\end{table}")


def render_vehicle_live_load_table(rows):
    return render_report_table(
        "Vehicle Live Loads (LL)", rows,
        header_rows=[
            ["Vehicle", "Total Load (kN)", "Impact Factor", ("Braking Load", 3)],
            ["", "", "", "Considered?", "Value", "Eccentricity"],
        ],
        header_clines={0: "4-6"},
        widths=[2.7, 2.0, 1.9, 2.3, 1.7, 2.2],
        align=["L", "C", "C", "C", "C", "C"], longtable=True, escape=False)


def render_analysis_demands_table(body_latex):
    header = r"""\hline
\multirow{2}{*}{\makecell{\textbf{Load}\\\textbf{Case/}\\\textbf{Comb.}}}
& \multicolumn{3}{c|}{\textbf{Bending Moment}}
& \multicolumn{3}{c|}{\textbf{Shear Force}}
& \multicolumn{2}{c|}{\textbf{Reaction at Supports}}\\
\cline{2-9}
& \makecell{\textbf{Max}\\\textbf{(kNm)}}
& \textbf{Girder}
& \makecell{\textbf{Loc.}\\\textbf{(m)}}
& \makecell{\textbf{Max}\\\textbf{(kN)}}
& \textbf{Girder}
& \makecell{\textbf{Loc.}\\\textbf{(m)}}
& \makecell{\textbf{Left}}
& \makecell{\textbf{Right}}\\
\hline
"""
    return (r"""\vspace{1em}
\begingroup
\footnotesize
\setlength{\tabcolsep}{3pt}
\renewcommand{\arraystretch}{1.25}
\setlength{\LTleft}{\dimexpr(\textwidth-17.8cm)/2\relax}
\setlength{\LTright}{\dimexpr(\textwidth-17.8cm)/2\relax}
\begin{longtable}{|
>{\centering\arraybackslash}p{3.1cm}|
>{\centering\arraybackslash}p{1.7cm}|
>{\centering\arraybackslash}p{1.2cm}|
>{\centering\arraybackslash}p{1.3cm}|
>{\centering\arraybackslash}p{1.7cm}|
>{\centering\arraybackslash}p{1.2cm}|
>{\centering\arraybackslash}p{1.3cm}|
>{\centering\arraybackslash}p{1.6cm}|
>{\centering\arraybackslash}p{1.6cm}|}
\captionsetup{justification=centering,font={small,it}}
\caption{Summary of Maximum Demands}\\
""" + header + r"""\endfirsthead
""" + header + r"""\endhead
""" + body_latex + r"""
\hline
\end{longtable}
\endgroup
""")


def render_parameter_value_table(caption, rows, longtable=False):
    return render_report_table(
        caption, rows, headers=["parameter", "value"], widths=[6.4, 8.6],
        align=["L", "L"], longtable=longtable, escape=False)


def render_grouped_report_table(caption, groups, headers=None, widths=None, align=None, escape=True,
                                longtable_min_rows=19):
    headers = headers or []
    groups = [(label, [list(row) for row in group_rows]) for label, group_rows in groups]
    rows = [[label] + row for label, group_rows in groups for row in group_rows]
    ncols, widths, align = _table_layout(headers, rows, widths, align)

    def _header(cell, width):
        text = str(cell or "")
        text = text[:1].upper() + text[1:] if text else text
        text = _tex(text) if escape else text
        return (r"\parbox[c][2.8\baselineskip][c]{" + str(width)
                + r"cm}{\centering\textbf{" + text + "}}")
    fmt = _tex if escape else str
    colspec = "|" + "|".join(f"{a}{{{w}cm}}" for a, w in zip(align, widths)) + "|"
    header = "\\hline\n" + " & ".join(_header(h, w) for h, w in zip(headers, widths)) + r" \\" + "\n\\hline\n"

    table_key = grouped_table_key(caption)

    def _row_marker(group_idx, row_idx, edge):
        return r"\noalign{\label{osdaggrp:" + table_key + ":" + str(group_idx) + ":" + str(row_idx) + ":" + edge + r"}}"

    def _group_tex(label, group_rows, group_idx=0, row_offset=0):
        out = []
        for idx, row in enumerate(group_rows):
            if _GROUPED_TABLE_PROBE:
                out.append(_row_marker(group_idx, row_offset + idx, "s"))
                first = fmt(label)
                line_end = r" \\"
            else:
                first = (r"\multirow{" + str(len(group_rows)) + "}{" + str(widths[0])
                         + r"cm}{\centering " + fmt(label) + "}") if idx == 0 else ""
                line_end = r" \\" if idx == len(group_rows) - 1 else r" \\*"
            line = " & ".join([first] + [fmt(cell) for cell in row]) + line_end
            out.append(line)
            if _GROUPED_TABLE_PROBE:
                out.append(_row_marker(group_idx, row_offset + idx, "e"))
            out.append(r"\hline" if _GROUPED_TABLE_PROBE or idx == len(group_rows) - 1 else f"\\cline{{2-{ncols}}}")
        return "\n".join(out)

    def _break_indexes(table_key, group_idx, group_rows):
        prefix = table_key + ":" + str(group_idx) + ":"
        indexes = sorted(
            int(marker[len(prefix):]) for marker in _GROUPED_TABLE_BREAKS
            if marker.startswith(prefix) and marker[len(prefix):].isdigit()
        )
        return [idx for idx in indexes if 0 < idx < len(group_rows)]

    def _visual_rows(cells):
        row_height = 1
        for cell, width in zip(cells, widths):
            text = str(cell or "").replace("\\allowbreak{}", "")
            for ch in "\\{}$_^":
                text = text.replace(ch, "")
            chars_per_line = max(8, int(width * 4.5))
            row_height = max(row_height, (len(text) + chars_per_line - 1) // chars_per_line)
        return row_height

    def _group_cost(label, group_rows):
        return sum(_visual_rows([label] + row) for row in group_rows)

    estimated_rows = sum(
        _visual_rows([label] + row) for label, group_rows in groups for row in group_rows
    )
    body_parts = []
    for group_idx, (label, group_rows) in enumerate(groups):
        breaks = _break_indexes(table_key, group_idx, group_rows)
        starts = [0] + breaks
        ends = breaks + [len(group_rows)]
        for chunk_idx, (start, end) in enumerate(zip(starts, ends)):
            chunk_rows = group_rows[start:end]
            if not _GROUPED_TABLE_PROBE:
                if chunk_idx > 0:
                    body_parts.append(r"\noalign{\penalty -10000}")
                else:
                    if group_idx == 0 and chunk_rows:
                        need = max(4, min(8, _visual_rows([label] + chunk_rows[0]) + 3))
                    else:
                        need = max(4, min(30, _group_cost(label, chunk_rows) + 2))
                    body_parts.append(r"\noalign{\needspace{" + str(need) + r"\baselineskip}}")
            body_parts.append(_group_tex(label, chunk_rows, group_idx, start))
    body = "\n".join(body_parts)
    caption_setup = r"\captionsetup{justification=centering,font={small,it}}"
    total_rows = sum(len(group_rows) for _, group_rows in groups)
    if total_rows < longtable_min_rows and estimated_rows < longtable_min_rows:
        need = max(6, min(34, estimated_rows + 5))
        return (r"\Needspace{" + str(need) + r"\baselineskip}" + "\n"
                + r"\begin{table}[H]" + "\n"
                + r"\centering" + "\n"
                + caption_setup + "\n" + r"\caption{" + _tex(caption) + "}\n"
                + r"\begin{tabular}{" + colspec + "}\n"
                + header + body + "\n"
                + r"\end{tabular}" + "\n"
                + r"\end{table}")

    start_label = (r"\label{osdaggrpstart:" + table_key + r"}" if _GROUPED_TABLE_PROBE else "")
    first_head = caption_setup + "\n" + r"\caption{" + _tex(caption) + r"}" + start_label + r"\\" + "\n" + header
    cont_head = (r"\multicolumn{" + str(ncols) + r"}{l}{\small\itshape Continued from previous page}\\"
                 + "\n" + header)
    cont_foot = (r"\multicolumn{" + str(ncols)
                 + r"}{r}{\small\itshape Continued on next page...}\\" + "\n")
    first_row_need = (_visual_rows([groups[0][0]] + groups[0][1][0]) if groups and groups[0][1] else 1)
    first_chunk_need = max(4, min(8, first_row_need + 3))
    start_guard = (r"\newpage" if (table_key + ":__start__") in _GROUPED_TABLE_BREAKS
                   else r"\Needspace{" + str(first_chunk_need) + r"\baselineskip}")
    return (start_guard + "\n"
            + r"\begin{longtable}{" + colspec + "}\n"
            + first_head + r"\endfirsthead" + "\n"
            + cont_head + r"\endhead" + "\n"
            + cont_foot + r"\endfoot" + "\n"
            + r"\hline" + "\n"
            + r"\endlastfoot" + "\n"
            + body + "\n"
            + r"\end{longtable}")


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
        label = input_dict.get(f"{KEY_MP_GD_SELECT_GIRDER}.G{i}") or f"G{i}"
        entries.append(
            (
                label,
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

def _fig_embed(path, caption, width=r'\textwidth', height=None, numbered=False):
    """Embed a real figure when path is provided (already copied); otherwise use an fbox placeholder."""
    if path:
        p = path.replace('\\', '/')
        opts = 'width=' + width
        if height:
            opts += ',height=' + height + ',keepaspectratio'
        cap_cmd = r'\caption' if numbered else r'\caption*'
        return (r'\begin{figure}[H]' + '\n'
                r'\vspace{-0.5em}' + '\n'
                r'\centering' + '\n'
                r'\includegraphics[' + opts + ']{' + p + '}\n'
                r'\vspace{0.5em}' + '\n'
                + cap_cmd + r'{\small ' + caption + '}\n'
                r'\vspace{-0.5em}' + '\n'
                r'\end{figure}')
    # fbox placeholder — matches template exactly
    return (r'\noindent\fbox{\parbox{0.97\textwidth}{' + '\n'
            r'\textit{[ PLACEHOLDER: ' + caption + r' ]}' + '\n'
            r'}}')


class ReportChartGenerator:
    """Generate temporary vector charts for report figures."""

    def __init__(self, output_dir, latex_dir="assets"):
        self.output_dir = output_dir
        self.latex_dir = latex_dir

    def _number(self, value):
        
        text = str(value or "").strip()
        if not text or text.upper() in {"N.A.", "NA", "N/A", "---"}:
            return 0.0
        text = text.replace(",", "")
        # Read LaTeX scientific notation correctly for very small BOQ values.
        sci = re.search(r"(-?\d+(?:\.\d+)?)\s*\\times\s*10\^\{(-?\d+)\}", text)
        if sci:
            return float(sci.group(1)) * (10.0 ** int(sci.group(2)))
        match = re.search(r"-?\d+(?:\.\d+)?", text)
        return float(match.group(0)) if match else 0.0

    def _first_number(self, quantities, keys):
        for key in keys:
            value = self._number(quantities.get(key))
            if value:
                return value
        return 0.0

    def _save_bar_chart(self, filename, labels, values, xlabel, ylabel, title, colors):
       
        os.makedirs(self.output_dir, exist_ok=True)
        os.environ.setdefault("MPLCONFIGDIR", os.path.join(self.output_dir, "mplconfig"))
        os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)
        
        matplotlib.use("Agg", force=True)
        matplotlib.rcParams["pdf.fonttype"] = 42
        matplotlib.rcParams["ps.fonttype"] = 42
        

        fig, ax = plt.subplots(figsize=(7.0, 3.8), dpi=220)
        bars = ax.bar(labels, values, color=colors, width=0.55)
        ax.set_title(title, fontsize=12, fontweight="bold", pad=10)
        ax.set_xlabel(xlabel, fontsize=10)
        ax.set_ylabel(ylabel, fontsize=10)
        ax.grid(axis="y", linestyle="--", linewidth=0.6, alpha=0.35)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ymax = max(values) if values else 0.0
        ax.set_ylim(0, ymax * 1.18 if ymax > 0 else 1)
        for bar, value in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                    f"{value:.2f}", ha="center", va="bottom", fontsize=9)
        fig.tight_layout()
        path = os.path.join(self.output_dir, filename)
        fig.savefig(path, format="pdf", bbox_inches="tight")
        plt.close(fig)
        return (self.latex_dir.rstrip("/\\") + "/" + filename).replace("\\", "/")

    def _save_ur_chart(self, filename, labels, values):
        
        os.makedirs(self.output_dir, exist_ok=True)
        os.environ.setdefault("MPLCONFIGDIR", os.path.join(self.output_dir, "mplconfig"))
        os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)
        
        matplotlib.use("Agg", force=True)
        matplotlib.rcParams["pdf.fonttype"] = 42
        matplotlib.rcParams["ps.fonttype"] = 42
        

        plot_values = [v if v is not None else 0.0 for v in values]
        colors = ["#b55353" if (v is not None and v > 1.0) else "#6aa84f" if v is not None else "#9e9e9e" for v in values]
        fig, ax = plt.subplots(figsize=(7.2, 3.8), dpi=220)
        bars = ax.bar(labels, plot_values, color=colors, width=0.55)
        ax.axhline(1.0, color="#c00000", linestyle="--", linewidth=1.3, label="UR = 1.0")
        ax.set_title("Utilization Ratio Summary", fontsize=12, fontweight="bold", pad=10)
        ax.set_xlabel("Primary Element", fontsize=10)
        ax.set_ylabel("Utilization Ratio (Demand / Capacity)", fontsize=10)
        ax.grid(axis="y", linestyle="--", linewidth=0.6, alpha=0.35)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.legend(loc="upper right", frameon=False, fontsize=9)
        ax.set_ylim(0, max(plot_values + [1.0]) * 1.22)
        for bar, value in zip(bars, values):
            label = "N/A" if value is None else f"{value:.2f}"
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                    label, ha="center", va="bottom", fontsize=9)
        fig.tight_layout()
        path = os.path.join(self.output_dir, filename)
        fig.savefig(path, format="pdf", bbox_inches="tight")
        plt.close(fig)
        return (self.latex_dir.rstrip("/\\") + "/" + filename).replace("\\", "/")

    def _max_dcr(self, data):
        best = None
        if isinstance(data, dict):
            for key, value in data.items():
                if str(key).lower() in {"dcr", "ur", "efficiency", "utilization", "utilization_ratio"}:
                    n = self._number(value)
                    if n > 0:
                        best = n if best is None else max(best, n)
                child = self._max_dcr(value)
                if child is not None:
                    best = child if best is None else max(best, child)
        elif isinstance(data, (list, tuple)):
            for item in data:
                child = self._max_dcr(item)
                if child is not None:
                    best = child if best is None else max(best, child)
        return best

    def generate_utilization_ratio_charts(self, bridge):
        try:
            output = bridge.output_dict or {}
            steel = self._max_dcr((output.get("design_results", {}) or {}).get("per_girder", {}))
            deck_rpt = output.get("deck_report_values", {}) or {}
            deck_values = []
            for demand_key, capacity_key in (
                ("deck.report.m_uls_sag", "deck.report.mu_bot"),
                ("deck.report.m_uls_hog", "deck.report.mu_top"),
                ("deck.report.punch_ved", "deck.report.vrd_c_mpa"),
                ("deck.report.shear_ved", "deck.report.shear_vrdc"),
                ("deck.report.wk_bot", "deck.report.wk_limit"),
                ("deck.report.wk_top", "deck.report.wk_limit"),
            ):
                demand = self._number(deck_rpt.get(demand_key))
                capacity = self._number(deck_rpt.get(capacity_key))
                if capacity > 0:
                    deck_values.append(demand / capacity)
            deck = max(deck_values) if deck_values else self._max_dcr(output.get("deck_design_results", {}))
            cb_values = []
            for pair in bridge.get_cb_pairs():
                for member in ("diagonal", "chord"):
                    for force_type in ("compression", "tension"):
                        n = self._number(bridge.get_cb_efficiency(pair, member, force_type))
                        if n > 0:
                            cb_values.append(n)
            cross_bracing = max(cb_values) if cb_values else self._max_dcr(output.get("crossbracing_design_results", {}))
            end_diaphragm = self._max_dcr(output.get("end_diaphragm_design_results", {}))
            return {"ur_summary": self._save_ur_chart(
                "utilization_ratio_summary.pdf",
                ["Steel Plate\nGirders", "Concrete\nDeck Slab", "Cross\nBracing", "End\nDiaphragms"],
                [steel, deck, cross_bracing, end_diaphragm])}
        except Exception:
            return {}

    def generate_material_quantity_charts(self, quantities):
        try:
            bracing = sum(self._number(quantities.get(key)) for key in (
                "bracing_top_wt_total", "bracing_bot_wt_total", "bracing_diag_wt_total"
            ))
            diaphragm = self._first_number(quantities, (
                "end_diaphragm_wt_total", "end_diaphragms_wt_total",
                "steel_end_diaphragm_wt_total", "steel_end_diaphragms_wt_total",
                "diaphragm_wt_total", "diaphragms_wt_total",
            ))
            return {
                "steel": self._save_bar_chart(
                    "material_steel_quantities.pdf",
                    ["Girders", "Cross Bracing", "End Diaphragms"],
                    [self._number(quantities.get("steel_girders_wt_total")), bracing, diaphragm],
                    "Structural Steel Component", "Weight (t)", "Structural Steel Tonnage",
                    ["#3b6ea8", "#6aa84f", "#c27c3a"]),
                "concrete_rebar": self._save_bar_chart(
                    "material_concrete_rebar_quantities.pdf",
                    ["Concrete Volume", "Reinforcement Steel"],
                    [self._number(quantities.get("concrete_deck_vol_total")),
                     self._number(quantities.get("rebar_deck_wt_total"))],
                    "Material Quantity Type", r"Quantity (m$^3$ / t)", "Concrete Volume and Reinforcement Steel",
                    ["#7a9cc6", "#b55353"]),
            }
        except Exception:
            return {}


