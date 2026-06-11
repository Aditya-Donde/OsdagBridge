import re
from collections import defaultdict

_bridge_results = []   # module-level list, reset each run

def pytest_configure(config):
    global _bridge_results
    _bridge_results = []

def pytest_runtest_logreport(report):
    if report.when != "call":
        return

    node = report.nodeid
    match = re.match(r"^(.*?)\[(.+)\]$", node)
    test_name  = match.group(1).split("::")[-1] if match else node.split("::")[-1]
    param_repr = match.group(2)                  if match else ""

    failure_reason = ""
    if report.failed:
        lines = [ln.strip() for ln in str(report.longrepr).splitlines() if ln.strip()]
        for ln in reversed(lines):
            if "AssertionError" in ln or "assert " in ln:
                failure_reason = ln[:200]
                break
        if not failure_reason and lines:
            failure_reason = lines[-1][:200]

    _bridge_results.append({
        "test_name": test_name,
        "params":    param_repr,
        "status":    report.outcome,
        "reason":    failure_reason,
    })

# ── Human-readable format description shown once per group ──────────────────
# Per-field validation interface: each test validates a single field and returns None (valid) or (value, message) (invalid)
HEADERS = {
    "test_validate_span": "span=<metres>  |  expect=VALID/INVALID",
    "test_validate_carriageway_width": "median=<Yes/No>  |  num_lanes=<int>  |  width=<metres>  |  expect=VALID/INVALID",
    "test_validate_skew_angle": "angle=<degrees>  |  expect=VALID/INVALID",
    "test_validate_ts_girder_spacing": "spacing=<metres>  |  overall_w=<metres>  |  expect=VALID/INVALID",
    "test_validate_ts_no_of_girders": "n_girders=<int>  |  overall_w=<metres>  |  expect=VALID/INVALID",
    "test_validate_ts_deck_overhang": "overhang=<metres>  |  overall_w=<metres>  |  expect=VALID/INVALID",
    "test_validate_ts_deck_thickness": "thickness=<mm>  |  expect=VALID/INVALID",
    "test_validate_ts_footpath_thickness": "thickness=<mm>  |  expect=VALID/INVALID",
    "test_validate_cb_width": "width=<metres>  |  overall_w=<metres>  |  expect=VALID/INVALID",
    "test_validate_cb_height": "height=<mm>  |  expect=VALID/INVALID",
    "test_validate_cb_load": "load=<kN>  |  expect=VALID/INVALID",
    "test_validate_cb_post_spacing": "spacing=<metres>  |  span=<metres>  |  expect=VALID/INVALID",
    "test_validate_md_width": "width=<metres>  |  overall_w=<metres>  |  expect=VALID/INVALID",
    "test_validate_md_height": "height=<mm>  |  expect=VALID/INVALID",
    "test_validate_md_load": "load=<kN>  |  expect=VALID/INVALID",
    "test_validate_md_post_spacing": "spacing=<metres>  |  span=<metres>  |  expect=VALID/INVALID",
    "test_validate_rl_height": "height=<mm>  |  expect=VALID/INVALID",
    "test_validate_rl_width": "width=<metres>  |  overall_w=<metres>  |  expect=VALID/INVALID",
    "test_validate_rl_load_value": "load=<kN>  |  expect=VALID/INVALID",
    "test_validate_wc_density": "density=<kg/m³>  |  expect=VALID/INVALID",
    "test_validate_wc_thickness": "thickness=<mm>  |  expect=VALID/INVALID",
    "test_validate_wc_ld_lane_table_count": "count=<int>  |  cw_width=<metres>  |  expect=VALID/INVALID",
    "test_validate_pl_self_weight_factor": "factor=<float>  |  expect=VALID/INVALID",
    "test_validate_ll_eccentricity": "eccentricity=<metres>  |  expect=VALID/INVALID",
    "test_validate_ll_footpath_pressure_value": "mode=<mode>  |  value=<kN/m²>  |  expect=VALID/INVALID",
    "test_validate_sl_importance_factor": "factor=<float>  |  expect=VALID/INVALID",
    "test_validate_sl_time_period": "period=<seconds>  |  expect=VALID/INVALID",
    "test_validate_sl_damping": "damping=<%>  |  expect=VALID/INVALID",
    "test_validate_sl_dead_load_value": "mode=<mode>  |  value=<float>  |  expect=VALID/INVALID",
    "test_validate_sl_live_load_value": "mode=<mode>  |  value=<float>  |  expect=VALID/INVALID",
    "test_validate_wl_avg_exposed_height": "height=<metres>  |  expect=VALID/INVALID",
    "test_validate_wl_gust_factor_value": "mode=<mode>  |  value=<float>  |  expect=VALID/INVALID",
    "test_validate_wl_drag_coeff_value": "mode=<mode>  |  value=<float>  |  expect=VALID/INVALID",
    "test_validate_wl_drag_coeff_ll_value": "mode=<mode>  |  value=<float>  |  expect=VALID/INVALID",
    "test_validate_wl_lift_coeff_value": "mode=<mode>  |  value=<float>  |  expect=VALID/INVALID",
    "test_validate_wl_super_area_elev_value": "mode=<mode>  |  value=<float>  |  expect=VALID/INVALID",
    "test_validate_wl_super_area_plain_value": "mode=<mode>  |  value=<float>  |  expect=VALID/INVALID",
    "test_validate_wl_exposed_frontal_value": "mode=<mode>  |  value=<float>  |  expect=VALID/INVALID",
    "test_validate_wl_wind_ecc_deck_value": "value=<float>  |  expect=VALID/INVALID",
    "test_validate_wl_wind_ll_ecc_value": "value=<float>  |  expect=VALID/INVALID",
    "test_validate_tl_thermal_coeff_steel": "coeff=<1/°C>  |  expect=VALID/INVALID",
    "test_validate_tl_thermal_coeff_rcc": "coeff=<1/°C>  |  expect=VALID/INVALID",
    "test_validate_ds_reinf_bounds": "bounds=<{dict}>  |  expect=VALID/INVALID",
    "test_validate_ds_top_clear_cover": "cover=<mm>  |  expect=VALID/INVALID",
    "test_validate_ds_bottom_clear_cover": "cover=<mm>  |  expect=VALID/INVALID",
    "test_validate_ds_side_clear_cover": "cover=<mm>  |  expect=VALID/INVALID",
    "test_validate_ds_stud_yield_strength": "strength=<MPa>  |  expect=VALID/INVALID",
    "test_validate_ds_stud_ultimate_strength": "strength=<MPa>  |  expect=VALID/INVALID",
    "test_validate_ds_stud_height": "height=<mm>  |  diameter=<mm>  |  deck_thickness=<mm>  |  expect=VALID/INVALID",
    "test_validate_ds_stud_count": "count=<int>  |  diameter=<mm>  |  flange_width=<metres>  |  expect=VALID/INVALID",
    "test_validate_ds_stud_transverse_spacing": "spacing=<mm>  |  diameter=<mm>  |  count=<int>  |  flange_width=<m>  |  expect=VALID/INVALID",
    "test_validate_partial_factors": "factor_key=<KEY_DO_GAMMA_*>  |  value=<float>  |  expect=VALID/INVALID",
    "test_validate_do_load_cycles": "cycles=<int>  |  expect=VALID/INVALID",
    "test_validate_do_deflection_limit": "limit=<mm>  |  expect=VALID/INVALID",
    "test_validate_additional_inputs_footpath_combinations_expanded": "footpath=<None/Single/Both>  |  kerb=<mm>  |  fp_width=<m>  |  railing=<mm>  |  expect=VALID/INVALID",
    "test_validate_stud_count_at_exact_maximum": "d=<mm>  |  flange=<m>  |  expected_max=<int>",
    "test_validate_stud_count_exceeding_maximum": "d=<mm>  |  flange=<m>  |  expected_max=<int>",
    "test_validate_stud_count_extreme_flange_very_small": "d=<mm>  |  flange=<m>",
    "test_validate_stud_transverse_spacing_below_minimum": "d=<mm>",
    "test_validate_stud_transverse_spacing_exceeds_maximum": "d=<mm>  |  flange=<m>  |  count=<int>",
    "test_validate_stud_transverse_spacing_impossible_geometry": "d=<mm>  |  flange=<m>  |  count=<int>",
    "test_validate_stud_transverse_spacing_max_boundary": "d=<mm>  |  flange=<m>  |  count=<int>",
    "test_validate_stud_transverse_spacing_min_boundary": "d=<mm>",
    "test_validate_stud_geometry_extreme_cases": "flange_m=<m>  |  d_mm=<mm>  |  count=<int>  |  spacing_mm=<mm>  |  expect=VALID/INVALID",
    "test_validate_stud_height_impossible_geometry_min_exceeds_max": "d=<mm>  |  dt=<mm>",
    "test_validate_footpath_width_edge_cases": "footpath=<None/Single/Both>  |  width=<m>  |  expect=VALID/INVALID",
    "test_validate_unbounded_load_values_pass_silently": "key=<KEY_*>  |  value=<float>",
    "test_validate_unbounded_thermal_coefficients_pass_silently": "key=<KEY_*>  |  value=<float>",
    "test_validate_no_of_girders_accepts_valid": "overall_w=<m>  |  girders=<int>",
    "test_validate_no_of_girders_rejects_invalid": "overall_w=<m>  |  girders=<int>",
    "test_carriageway_median_cross_field": "cw_width=<m>  |  median=<Yes/No>  |  expect=VALID/INVALID",
    "test_cross_field_span_carriageway_interaction": "span=<m>  |  cw=<m>  |  median=<Yes/No>  |  span_err=<bool>  |  cw_err=<bool>",
}

def _fmt(test_name: str, raw: str) -> str:
    """Convert raw pytest param-id string into a labelled, human-readable line."""
    parts = raw.split("-")

    def _clean(v: str) -> str:
        return re.sub(r"\d+$", "", v).lower()

    def _bool(v: str) -> str:   # True/False → VALID/INVALID
        return "VALID" if _clean(v) == "true" else "INVALID"

    def _unit(v: str, unit: str) -> str:
        clean_val = str(v).strip()
        if clean_val.lower() in ("none", "null"):
            return "None"
        return f"{clean_val}{unit}"

    try:
        if test_name == "test_validate_span":
            val = "-".join(parts[:-1])
            return f"span={val}  |  expect={_bool(parts[-1])}"

        if test_name == "test_validate_carriageway_width":
            if len(parts) >= 4:
                return f"median={parts[0]}  |  num_lanes={parts[1]}  |  width={'-'.join(parts[2:-1])}m  |  expect={_bool(parts[-1])}"

        if test_name == "test_validate_skew_angle":
            val = "-".join(parts[:-1])
            return f"angle={val}°  |  expect={_bool(parts[-1])}"

        if test_name in (
            "test_validate_ts_girder_spacing",
            "test_validate_ts_no_of_girders",
            "test_validate_ts_deck_overhang",
            "test_validate_cb_width",
            "test_validate_md_width",
            "test_validate_rl_width"
        ):
            if len(parts) >= 3:
                val = "-".join(parts[:-2])
                overall_w = parts[-2]
                return f"value={_unit(val, '')}  |  overall_w={_unit(overall_w, 'm')}  |  expect={_bool(parts[-1])}"

        if test_name in (
            "test_validate_cb_post_spacing",
            "test_validate_md_post_spacing",
        ):
            if len(parts) >= 3:
                val = "-".join(parts[:-2])
                span = parts[-2]
                return f"spacing={_unit(val, 'm')}  |  span={_unit(span, 'm')}  |  expect={_bool(parts[-1])}"

        if test_name == "test_validate_wc_ld_lane_table_count":
            if len(parts) >= 3:
                return f"count={parts[0]}  |  cw_width={_unit(parts[1], 'm')}  |  expect={_bool(parts[-1])}"

        if test_name in (
            "test_validate_ll_footpath_pressure_value",
            "test_validate_sl_dead_load_value",
            "test_validate_sl_live_load_value",
            "test_validate_wl_gust_factor_value",
            "test_validate_wl_drag_coeff_value",
            "test_validate_wl_drag_coeff_ll_value",
            "test_validate_wl_lift_coeff_value",
            "test_validate_wl_super_area_elev_value",
            "test_validate_wl_super_area_plain_value",
            "test_validate_wl_exposed_frontal_value"
        ):
            if len(parts) >= 3:
                return f"mode={parts[0]}  |  value={'-'.join(parts[1:-1])}  |  expect={_bool(parts[-1])}"

        if test_name == "test_validate_ds_stud_height":
            if len(parts) >= 4:
                return f"height={_unit('-'.join(parts[:-3]), 'mm')}  |  d={_unit(parts[-3], 'mm')}  |  dt={_unit(parts[-2], 'mm')}  |  expect={_bool(parts[-1])}"

        if test_name == "test_validate_ds_stud_count":
            if len(parts) >= 4:
                return f"count={parts[0]}  |  d={_unit(parts[1], 'mm')}  |  fw={_unit(parts[2], 'm')}  |  expect={_bool(parts[-1])}"

        if test_name == "test_validate_ds_stud_transverse_spacing":
            if len(parts) >= 5:
                return f"spacing={_unit('-'.join(parts[:-4]), 'mm')}  |  d={_unit(parts[-4], 'mm')}  |  count={parts[-3]}  |  fw={_unit(parts[-2], 'm')}  |  expect={_bool(parts[-1])}"
                
        if test_name == "test_validate_stud_geometry_extreme_cases":
            if len(parts) >= 5:
                return f"flange_m={_unit(parts[0], 'm')}  |  d_mm={_unit(parts[1], 'mm')}  |  count={parts[2]}  |  spacing_mm={_unit(parts[3], 'mm')}  |  expect={_bool(parts[-1])}"

        if test_name == "test_validate_additional_inputs_footpath_combinations_expanded":
            if len(parts) >= 5:
                exp = "VALID" if _clean(parts[-1]) == "true" else "INVALID"
                return f"footpath={parts[0]}  |  kerb={_unit(parts[1], 'mm')}  |  fp_width={_unit(parts[2], 'm')}  |  railing={_unit(parts[3], 'm')}  |  expect={exp}"

        if test_name == "test_validate_footpath_width_edge_cases":
            if len(parts) >= 3:
                return f"footpath={parts[0]}  |  width={_unit(parts[1], 'm')}  |  expect={_bool(parts[-1])}"

        if test_name in ("test_validate_no_of_girders_accepts_valid", "test_validate_no_of_girders_rejects_invalid"):
            if len(parts) >= 2:
                return f"overall_w={_unit(parts[0], 'm')}  |  girders={parts[1]}"

        if test_name == "test_carriageway_median_cross_field":
            if len(parts) >= 3:
                exp = "INVALID" if _clean(parts[-1]) == "true" else "VALID"
                return f"cw_width={parts[0]}m  |  median={parts[1]}  |  expect={exp}"

        if test_name == "test_cross_field_span_carriageway_interaction":
            if len(parts) >= 5:
                return f"span={parts[0]}m  |  cw={parts[1]}m  |  median={parts[2]}  |  span_err={parts[3]}  |  cw_err={parts[4]}"

        # Generic 2-param handler for simple value tests
        if test_name in (
            "test_validate_ts_deck_thickness",
            "test_validate_ts_footpath_thickness",
            "test_validate_cb_height",
            "test_validate_cb_load",
            "test_validate_md_height",
            "test_validate_md_load",
            "test_validate_rl_height",
            "test_validate_rl_load_value",
            "test_validate_wc_density",
            "test_validate_wc_thickness",
            "test_validate_pl_self_weight_factor",
            "test_validate_ll_eccentricity",
            "test_validate_sl_importance_factor",
            "test_validate_sl_time_period",
            "test_validate_sl_damping",
            "test_validate_wl_avg_exposed_height",
            "test_validate_wl_wind_ecc_deck_value",
            "test_validate_wl_wind_ll_ecc_value",
            "test_validate_tl_thermal_coeff_steel",
            "test_validate_tl_thermal_coeff_rcc",
            "test_validate_ds_reinf_bounds",
            "test_validate_ds_top_clear_cover",
            "test_validate_ds_bottom_clear_cover",
            "test_validate_ds_side_clear_cover",
            "test_validate_ds_stud_yield_strength",
            "test_validate_ds_stud_ultimate_strength",
            "test_validate_do_load_cycles",
            "test_validate_do_deflection_limit",
        ):
            if len(parts) >= 2:
                val = "-".join(parts[:-1])
                return f"value={_unit(val, '')}  |  expect={_bool(parts[-1])}"

    except Exception:
        pass

    return raw   # fallback: show raw param string unchanged

# ── Terminal summary hook ────────────────────────────────────────────────────
def pytest_terminal_summary(terminalreporter, exitstatus, config):
    if not _bridge_results:
        return

    groups = defaultdict(list)
    for r in _bridge_results:
        groups[r["test_name"]].append(r)

    total_all  = len(_bridge_results)
    passed_all = sum(1 for r in _bridge_results if r["status"] == "passed")
    failed_all = total_all - passed_all

    terminalreporter.write_sep("=", "Detailed Test Summary (per value)")

    for test_name, entries in groups.items():
        grp_passed = [e for e in entries if e["status"] == "passed"]
        grp_failed = [e for e in entries if e["status"] == "failed"]

        if not grp_failed:
            status_label = f"  ALL PASS ({len(grp_passed)}/{len(entries)})"
        else:
            status_label = f"  FAIL  {len(grp_failed)} failed / {len(entries)} total"

        terminalreporter.write_line(f"\n{test_name}{status_label}")
        terminalreporter.write_line("  " + "-" * 70)

        # Print the human-readable format description for this group
        if test_name in HEADERS:
            terminalreporter.write_line(f"  FORMAT: {HEADERS[test_name]}")
            terminalreporter.write_line("  " + "-" * 70)

        for e in entries:
            icon   = "PASS" if e["status"] == "passed" else "FAIL"
            params = _fmt(test_name, e["params"]) if e["params"] else "(no params)"
            line   = f"  [{icon}]  {params}"
            if e["reason"]:
                line += f"\n         -> {e['reason']}"
            terminalreporter.write_line(line)

    terminalreporter.write_sep("=", "End of Detailed Summary")
    terminalreporter.write_line("============================================================")
    terminalreporter.write_line(f"  TOTAL: {total_all}   PASSED: {passed_all}   FAILED: {failed_all}")
    terminalreporter.write_line("============================================================")
