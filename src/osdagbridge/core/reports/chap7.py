from osdagbridge.core.reports.report_utils import _fig_embed, render_report_table


def _wrap_multiply(value):
    text = str(value)
    times = r"\allowbreak{}\times\allowbreak{}" if "$" in text else r"\allowbreak{}$\times$\allowbreak{}"
    return text.replace(r"\times", r"\allowbreak{}\times\allowbreak{}").replace("×", times).replace(" x ", f" {times} ")


def _qty_header(text):
    return r"\parbox[t][1.75cm][c]{\linewidth}{\centering " + text + "}"


def ch7_quantities(input_dict, output_dict=None, chart_paths=None):
    if chart_paths is None and isinstance(output_dict, dict) and (
            "steel" in output_dict or "concrete_rebar" in output_dict):
        chart_paths, output_dict = output_dict, None
    chart_paths = chart_paths or {}
    chart_figures = ""
    if chart_paths:
        chart_figures = (
            "\n\\vspace{1em}\n"
            + _fig_embed(chart_paths.get("steel"),
                         "Structural Steel Tonnage Summary",
                         width=r"0.82\textwidth", numbered=True)
            + "\n\\vspace{0.5em}\n"
            + _fig_embed(chart_paths.get("concrete_rebar"),
                         "Concrete Volume and Reinforcement Steel Summary",
                         width=r"0.82\textwidth", numbered=True)
        )
    rows = [
        ["1", "Structural Steel (IS 2062) for Girders", _wrap_multiply(input_dict.get("steel_girders_vol_formula", "N.A.")), input_dict.get("steel_girders_qty", "N.A."), input_dict.get("steel_girders_vol_total", "N.A."), input_dict.get("steel_girders_wt_single", "N.A."), input_dict.get("steel_girders_wt_total", "N.A.")],
        ["2(a)", "Cross Bracing - Top Chord", _wrap_multiply(input_dict.get("bracing_top_vol_formula", "N.A.")), input_dict.get("bracing_top_qty", "N.A."), input_dict.get("bracing_top_vol_total", "N.A."), input_dict.get("bracing_top_wt_single", "N.A."), input_dict.get("bracing_top_wt_total", "N.A.")],
        ["2(b)", "Cross Bracing - Bottom Chord", _wrap_multiply(input_dict.get("bracing_bot_vol_formula", "N.A.")), input_dict.get("bracing_bot_qty", "N.A."), input_dict.get("bracing_bot_vol_total", "N.A."), input_dict.get("bracing_bot_wt_single", "N.A."), input_dict.get("bracing_bot_wt_total", "N.A.")],
        ["2(c)", "Cross Bracing - Diagonal Chord", _wrap_multiply(input_dict.get("bracing_diag_vol_formula", "N.A.")), input_dict.get("bracing_diag_qty", "N.A."), input_dict.get("bracing_diag_vol_total", "N.A."), input_dict.get("bracing_diag_wt_single", "N.A."), input_dict.get("bracing_diag_wt_total", "N.A.")],
        ["3(a)", "Stiffeners - Bearing", _wrap_multiply(input_dict.get("stiffener_bearing_vol_formula", "N.A.")), input_dict.get("stiffener_bearing_qty", "N.A."), input_dict.get("stiffener_bearing_vol_total", "N.A."), input_dict.get("stiffener_bearing_wt_single", "N.A."), input_dict.get("stiffener_bearing_wt_total", "N.A.")],
        ["3(b)", "Stiffeners - Intermediate", _wrap_multiply(input_dict.get("stiffener_int_vol_formula", "N.A.")), input_dict.get("stiffener_int_qty", "N.A."), input_dict.get("stiffener_int_vol_total", "N.A."), input_dict.get("stiffener_int_wt_single", "N.A."), input_dict.get("stiffener_int_wt_total", "N.A.")],
        ["4", "Connections", _wrap_multiply(input_dict.get("connections_vol_formula", "N.A.")), input_dict.get("connections_qty", "N.A."), input_dict.get("connections_vol_total", "N.A."), input_dict.get("connections_wt_single", "N.A."), input_dict.get("connections_wt_total", "N.A.")],
        ["5", "Concrete (M40) for Deck Slab", _wrap_multiply(input_dict.get("concrete_deck_vol_formula", "N.A.")), input_dict.get("concrete_deck_qty", "N.A."), input_dict.get("concrete_deck_vol_total", "N.A."), input_dict.get("concrete_deck_wt_single", "N.A."), input_dict.get("concrete_deck_wt_total", "N.A.")],
        ["6", "Reinforcement Steel (Fe 500)", _wrap_multiply(input_dict.get("rebar_deck_vol_formula", "N.A.")), input_dict.get("rebar_deck_qty", "N.A."), input_dict.get("rebar_deck_vol_total", "N.A."), input_dict.get("rebar_deck_wt_single", "N.A."), input_dict.get("rebar_deck_wt_total", "N.A.")],
        ["7", "Shear Stud Connectors", _wrap_multiply(input_dict.get("shear_studs_vol_formula", "N.A.")), input_dict.get("shear_studs_qty", "N.A."), input_dict.get("shear_studs_vol_total", "N.A."), input_dict.get("shear_studs_wt_single", "N.A."), input_dict.get("shear_studs_wt_total", "N.A.")],
        ["8", "Crash Barrier", _wrap_multiply(input_dict.get("crash_barrier_vol_formula", "N.A.")), input_dict.get("crash_barrier_qty", "N.A."), input_dict.get("crash_barrier_vol_total", "N.A."), input_dict.get("crash_barrier_wt_single", "N.A."), input_dict.get("crash_barrier_wt_total", "N.A.")],
    ]
    return r"""
\chapter{Bill of Materials}
\label{ch:material-takeoff}
""" + render_report_table(
        "Bill of Materials for Superstructure", rows,
        header_rows=[[_qty_header("S.N."), _qty_header(r"Item\\Description"),
                      _qty_header("Volume"), _qty_header("Quantity"),
                      _qty_header(r"Total\\Volume\\(m$^3$)"),
                      _qty_header(r"Weight\\(t)"), _qty_header(r"Total\\Weight\\(t)")]],
        widths=[1.0, 3.8, 2.5, 2.1, 1.8, 1.7, 1.8],
        align=["C", "L", "C", "C", "C", "C", "C"],
        longtable=True, escape=False) + chart_figures


