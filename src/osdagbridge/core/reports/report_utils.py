from osdagbridge.core.utils.common import (
    KEY_MP_GD_MEMBER_ID,
    KEY_MP_GD_SELECT_GIRDER,
    KEY_MP_GIRDER_DEPTH,
    KEY_TS_NO_OF_GIRDERS
)


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


def render_report_table(caption, rows, headers=None, widths=None, align=None, longtable=False, escape=True):
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
    align = align or ["L"] * ncols

    def _header(cell):
        text = str(cell or "")
        text = text[:1].upper() + text[1:] if text else text
        return r"\textbf{" + (_tex(text) if escape else text) + "}"
    colspec = "|" + "|".join(f"{a}{{{w}cm}}" for a, w in zip(align, widths)) + "|"
    header = ""
    if headers:
        header_row = " & ".join(_header(h) for h in headers) + r" \\"
        header = "\\hline\n" + header_row + "\n\\hline\n"
    fmt = _tex if escape else str
    body = "\n".join(" & ".join(fmt(cell) for cell in row) + r" \\" + "\n\\hline" for row in rows)

    if longtable:
        repeat = (header + "\\endfirsthead\n" + header + "\\endhead\n") if headers and len(rows) > 12 else (header or "\\hline\n")
        return ("\\begin{longtable}{" + colspec + "}\n" + repeat + body
                + "\n\\captionsetup{justification=centering,font={small,it}}\n\\caption{"
                + _tex(caption) + "}\\\\\n\\end{longtable}")

    return ("\\begin{table}[H]\n\\centering\n\\begin{tabular}{" + colspec
            + "}\n" + (header or "\\hline\n") + body
            + "\n\\end{tabular}\n\\captionsetup{justification=centering,font={small,it}}\n\\caption{"
            + _tex(caption) + "}\n\\end{table}")


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
                r'\vspace{0.5em}' + '\n'
                r'\caption*{\small ' + caption + '}\n'
                r'\vspace{-0.5em}' + '\n'
                r'\end{figure}')
    # fbox placeholder — matches template exactly
    return (r'\noindent\fbox{\parbox{0.97\textwidth}{' + '\n'
            r'\textit{[ PLACEHOLDER: ' + caption + r' ]}' + '\n'
            r'}}')


