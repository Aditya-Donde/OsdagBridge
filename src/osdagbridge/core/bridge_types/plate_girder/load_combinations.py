"""
IRC:6-2017 ULS / SLS load-combination expansion shared by the desktop
load-combination widget and the plate-girder backend.

Lives in core (not the UI) so ``plategirderbridge`` can build the
authoritative combinations list without importing PySide6.
"""
from __future__ import annotations

from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017

# ── Load abbreviation map (same symbols as the analyser's LOAD_ABBR) ─────
_ABBREV = {
    'dead_load':    'DL',
    'surfacing':    'DW',
    'live_load':    'LL',
    'wind_load':    'WL',
    'thermal_load': 'TL',
    'seismic':      'EL',
}
_VARIABLE_LOADS   = ['live_load', 'wind_load', 'thermal_load']
_ACCIDENTAL_LOADS = ['vehicle_collision', 'barge_impact', 'floating_bodies']
_DIRECTIONS       = ['adding', 'relieving']


def default_load_combination_entries() -> list[dict]:
    """
    Expand the IRC:6-2017 ULS + SLS load combinations into display entries.

    Walks the *same* Table B.2 / B.3 lookups (``IRC6_2017.table_B2`` /
    ``table_B3``) and the same key tuples (``ULS_COMBINATION_KEYS`` /
    ``SLS_COMBINATION_KEYS``) as ``BridgeGrillageModel.create_uls_combinations``
    / ``create_sls_combinations``, in the same order, so the widget lists
    exactly the combinations the analyser builds. The analyser then names
    its load cases from this list (``name_by_key``), so the widget, the
    analysis load cases and the results table all carry one string. Each
    entry is::

        {"name": "<PREFIX>_<n> : <expr>", "included": True, "key": <str>, "expr": <str>}

    ``included`` defaults to True; callers overlay the user's selection.
    """
    abbr     = _ABBREV
    entries  = []
    counters = {}

    def _add(prefix, key, factors):
        # Skip None / 0 factors, exactly as the analyser's _copy_loads does.
        expr = ' + '.join(
            f"{fac}{abbr[load]}" for load, fac in factors.items()
            if fac is not None and fac != 0
        )
        counters[prefix] = seq = counters.get(prefix, 0) + 1
        entries.append({
            'name':     f"{prefix}_{seq} : {expr}",
            'included': True,
            'key':      key,
            'expr':     expr,
        })

    # ── ULS (Table B.2) — mirrors create_uls_combinations ────────────────
    γ = IRC6_2017.table_B2

    # BASIC: 2 permanent directions × 3 variable loads as leading
    for direction in _DIRECTIONS:
        perm = {'dead_load': γ('dead_load', direction, 'basic'),
                'surfacing': γ('surfacing', direction, 'basic')}
        for leading in _VARIABLE_LOADS:
            var = {vl: γ(vl, 'leading' if vl == leading else 'accompanying', 'basic')
                   for vl in _VARIABLE_LOADS}
            if var[leading] is None:
                continue
            _add('BASIC',
                 IRC6_2017.ULS_COMBINATION_KEYS.get(('basic', leading, None, direction), ''),
                 {**perm, **var})

    # ACCIDENTAL: 3 events × 1 valid leading (DL/DW γ=1.0 both ways → one direction)
    perm = {'dead_load': γ('dead_load', 'adding', 'accidental'),
            'surfacing': γ('surfacing', 'adding', 'accidental')}
    for acc in _ACCIDENTAL_LOADS:
        for leading in _VARIABLE_LOADS:
            var = {vl: γ(vl, 'leading' if vl == leading else 'accompanying', 'accidental')
                   for vl in _VARIABLE_LOADS}
            if var[leading] is None:
                continue
            _add('ACCIDENTAL',
                 IRC6_2017.ULS_COMBINATION_KEYS.get(('accidental', leading, acc, 'adding'), ''),
                 {**perm, **var})

    # SEISMIC: 2 permanent directions × 2 conditions
    var_seis = {vl: γ(vl, 'accompanying', 'seismic') for vl in _VARIABLE_LOADS}
    for direction in _DIRECTIONS:
        perm = {'dead_load': γ('dead_load', direction, 'seismic'),
                'surfacing': γ('surfacing', direction, 'seismic')}
        for condition in ['service', 'construction']:
            _add('SEISMIC',
                 IRC6_2017.ULS_COMBINATION_KEYS.get(('seismic', condition, None, direction), ''),
                 {**perm, **var_seis, 'seismic': γ('seismic', condition, 'seismic')})

    # ── SLS (Table B.3) — mirrors create_sls_combinations ────────────────
    γ = IRC6_2017.table_B3

    # RARE & FREQUENT: 2 surfacing directions × 3 variable loads as leading
    for combo_type, prefix in [('rare', 'SLS_RARE'), ('frequent', 'SLS_FREQUENT')]:
        dl_f = γ('dead_load', None, combo_type)       # always 1.0 in SLS
        for direction in _DIRECTIONS:
            dw_f = γ('surfacing', direction, combo_type)
            for leading in _VARIABLE_LOADS:
                var = {vl: γ(vl, 'leading' if vl == leading else 'accompanying', combo_type)
                       for vl in _VARIABLE_LOADS}
                if var[leading] is None:
                    continue
                _add(prefix,
                     IRC6_2017.SLS_COMBINATION_KEYS.get((combo_type, leading, direction), ''),
                     {'dead_load': dl_f, 'surfacing': dw_f, **var})

    # QUASI-PERMANENT: adding & relieving surfacing; only TL contributes
    dl_f   = γ('dead_load', None, 'quasi_permanent')
    var_qp = {vl: γ(vl, 'accompanying', 'quasi_permanent') for vl in _VARIABLE_LOADS}
    for direction in _DIRECTIONS:
        _add('SLS_QP',
             IRC6_2017.SLS_COMBINATION_KEYS.get(('quasi_permanent', None, direction), ''),
             {'dead_load': dl_f, 'surfacing': γ('surfacing', direction, 'quasi_permanent'), **var_qp})

    return entries


def build_load_combinations(saved_selection, custom_combinations) -> list[dict]:
    """
    Build the authoritative load-combinations list for the results table.

    Regenerates the IRC:6 default combinations
    (`default_load_combination_entries`), overlays the user's
    include/exclude selection (matched by key), then
    appends the user's custom combinations. Each returned entry is
    ``{"name", "expr", "included", "key"}`` (custom entries have no key).

    Parameters
    ----------
    saved_selection : list[dict] | None
        The per-combination selection saved by the load-combination widget
        (each ``{"key", "name", "included", ...}``).
    custom_combinations : list[dict] | None
        User-defined combinations (each ``{"name", "included", "items"}``,
        where each item is ``{"case", "factor"}``).
    """
    entries = default_load_combination_entries()

    sel_by_key = {e.get("key"): e.get("included") for e in saved_selection
                  if isinstance(e, dict) and e.get("key")}
    for e in entries:
        if e["key"] in sel_by_key:
            e["included"] = bool(sel_by_key[e["key"]])

    combos = [
        {"name": e["name"], "expr": e["expr"], "included": e["included"], "key": e["key"]}
        for e in entries
    ]

    for c in (custom_combinations):
        if not isinstance(c, dict):
            continue
        items = c.get("items")
        expr  = " + ".join(
            f"{i.get('factor', '')}{i.get('case', '')}"
            for i in items if isinstance(i, dict)
        )
        combos.append({
            "name":     str(c.get("name", "Custom")),
            "expr":     expr,
            "included": bool(c.get("included", True)),
        })

    return combos
