from osdagbridge.desktop.ui.dialogs.tabs.additional_inputs.typical_section_details import TypicalSectionDetailsTab


def test_typical_section_round_trip(qapp):
    tab = TypicalSectionDetailsTab()
    qapp.processEvents()

    snapshot = tab.collect_data()
    assert isinstance(snapshot, dict)

    tab.restore_data(snapshot)
    qapp.processEvents()

    tab.reset_defaults()
    qapp.processEvents()

    errors = tab.validate_tab()
    assert isinstance(errors, list)


def test_typical_section_reset_restores_schema_owned_fields(qapp):
    tab = TypicalSectionDetailsTab()
    qapp.processEvents()

    tab.deck_thickness.setText("275")
    tab.footpath_width.setText("2.25")
    tab.footpath_thickness.setText("250")
    tab.wearing_thickness.setText("90")

    tab.reset_defaults()
    qapp.processEvents()

    assert tab.deck_thickness.text() == "200"
    assert tab.footpath_width.text() == "1.50"
    assert tab.footpath_thickness.text() == "200"
    assert tab.wearing_thickness.text() == "50"


def test_layout_notice_api_and_lane_state(qapp):
    tab = TypicalSectionDetailsTab()
    qapp.processEvents()

    tab.layout_tab.set_notices(reason="spacing adjusted", warning="check overhang")
    assert not tab.layout_tab.layout_notice_container.isHidden()
    assert "spacing adjusted" in tab.layout_tab.layout_adjust_notice.text()

    snapshot = tab.collect_data()
    lane_rows = snapshot.get("lane_table_data", [])
    assert isinstance(lane_rows, list)
    assert lane_rows == tab.lane_details_tab.get_lane_rows()

    tab.layout_tab.clear_notices()
    assert tab.layout_tab.layout_notice_container.isHidden()

    applied = tab.layout_tab.apply_layout_solution(2.5, 0.88, 2)
    assert applied["girder_spacing_m"] == 2.5
    assert tab.girder_spacing.text() == "2.50"
    assert tab.deck_overhang.text() == "0.88"
    assert tab.no_of_girders.text() == "2"

    tab.layout_tab.clear_layout_fields()
    assert tab.girder_spacing.text() == ""
    assert tab.deck_overhang.text() == ""
    assert tab.no_of_girders.text() == ""

    tab.layout_tab.apply_layout_solution(2.5, 0.88, 2)
    change = tab.layout_tab.handle_layout_field_change(changed_field="spacing")
    assert change.get("ok") is False
    assert change.get("unchanged") is True


def test_lane_details_child_api_round_trip(qapp):
    tab = TypicalSectionDetailsTab()
    qapp.processEvents()

    rows = [
        {"lane_number": "1", "start": "0.00", "width": "3.50"},
        {"lane_number": "2", "start": "3.50", "width": "3.50"},
    ]
    tab.lane_details_tab.set_lane_rows(rows)
    qapp.processEvents()

    assert tab.lane_details_tab.get_lane_rows() == rows
    assert tab.lane_details_tab.export_lane_table_state()["lane_table_data"] == rows


def test_lane_details_child_owns_defaults_and_selection(qapp):
    tab = TypicalSectionDetailsTab()
    tab.set_bridge_context(carriageway_width=7.5)
    qapp.processEvents()

    lane_tab = tab.lane_details_tab
    assert lane_tab.lane_count_combo.count() == 2
    assert lane_tab.lane_count_combo.currentText() == "2"
    assert lane_tab.get_lane_rows() == [
        {"lane_number": "1", "start": "0.00", "width": "3.50"},
        {"lane_number": "2", "start": "3.50", "width": "3.50"},
    ]

    lane_tab.lane_count_combo.setCurrentText("1")
    qapp.processEvents()

    assert lane_tab.get_lane_rows() == [
        {"lane_number": "1", "start": "0.00", "width": "3.50"},
    ]


def test_lane_details_syncs_to_actual_carriageway_width(qapp):
    tab = TypicalSectionDetailsTab()
    tab.set_bridge_context(carriageway_width=4.25)
    qapp.processEvents()

    lane_tab = tab.lane_details_tab

    assert lane_tab.lane_count_combo.count() == 1
    assert lane_tab.lane_count_combo.currentText() == "1"
    assert lane_tab.get_lane_rows() == [
        {"lane_number": "1", "start": "0.00", "width": "3.50"},
    ]
    assert lane_tab.validate_tab() == []

    lane_tab.lane_count_combo.setCurrentText("2")
    qapp.processEvents()

    assert lane_tab.lane_count_combo.currentText() == "1"
    assert lane_tab.table.rowCount() == 1


def test_lane_details_rebuilds_choices_when_bridge_width_changes(qapp):
    tab = TypicalSectionDetailsTab()
    qapp.processEvents()

    lane_tab = tab.lane_details_tab
    assert lane_tab.lane_count_combo.count() == 2

    tab.set_bridge_context(carriageway_width=14.0)
    qapp.processEvents()

    assert [lane_tab.lane_count_combo.itemText(i) for i in range(lane_tab.lane_count_combo.count())] == [
        "1",
        "2",
        "3",
        "4",
    ]
    assert lane_tab.lane_count_combo.currentText() == "4"
    assert lane_tab.table.rowCount() == 4


def test_lane_details_restore_clamps_rows_to_bridge_width(qapp):
    tab = TypicalSectionDetailsTab()
    tab.set_bridge_context(carriageway_width=4.25)
    qapp.processEvents()

    tab.lane_details_tab.restore_data({
        "lane_table_data": [
            {"lane_number": "1", "start": "0.00", "width": "3.50"},
            {"lane_number": "2", "start": "3.50", "width": "3.50"},
        ]
    })
    qapp.processEvents()

    assert tab.lane_details_tab.lane_count_combo.currentText() == "1"
    assert tab.lane_details_tab.get_lane_rows() == [
        {"lane_number": "1", "start": "0.00", "width": "3.50"},
    ]


def test_typical_section_subtab_state_exports(qapp):
    tab = TypicalSectionDetailsTab()
    qapp.processEvents()

    assert isinstance(tab.crash_barrier_tab.export_barrier_state(), dict)
    assert isinstance(tab.median_tab.export_median_state(include_median=True), dict)
    assert isinstance(tab.railing_tab.export_railing_state(), dict)
    assert isinstance(tab.wearing_course_tab.export_wearing_state(), dict)


def test_typical_section_subtab_cad_exports(qapp):
    tab = TypicalSectionDetailsTab()
    qapp.processEvents()

    bridge_params = tab.layout_tab.export_bridge_context_cad_params(
        tab.carriageway_width,
        tab.footpath_value,
    )
    layout_params = tab.layout_tab.export_cad_params()
    crash_params = tab.crash_barrier_tab.export_cad_params()
    median_params = tab.median_tab.export_cad_params(include_median=True)
    railing_params = tab.railing_tab.export_cad_params()
    wearing_params = tab.wearing_course_tab.export_cad_params()

    assert isinstance(bridge_params, dict)
    assert isinstance(layout_params, dict)
    assert isinstance(crash_params, dict)
    assert isinstance(median_params, dict)
    assert isinstance(railing_params, dict)
    assert isinstance(wearing_params, dict)
    assert "footpath_config" in bridge_params
    assert "num_girders" in layout_params
    assert "median_present" in median_params


def test_layout_tab_solver_plan(qapp):
    tab = TypicalSectionDetailsTab()
    qapp.processEvents()

    overall_width = tab.get_overall_bridge_width()
    spacing_bounds = tab._spacing_bounds(overall_width)
    plan = tab.layout_tab.solve_layout_plan(
        overall_width=overall_width,
        changed_field="width",
        spacing_bounds=spacing_bounds,
        default_spacing=2.5,
    )

    assert plan["ok"] is True
    assert isinstance(plan["solution"], dict)
    assert set(plan["solution"]) == {"spacing", "overhang", "girders"}


def test_typical_section_child_sync_helpers_return_cad_payloads(qapp):
    tab = TypicalSectionDetailsTab()
    qapp.processEvents()

    crash_geom = {"bottom_width": 450.0, "total_height": 900.0}
    crash_params = tab.crash_barrier_tab.sync_from_parent_geometry(
        "IRC 5 - RCC Crash Barrier",
        crash_geom,
        force=True,
    )
    median_geom = {"median_width": 1200.0, "kerb_height": 450.0}
    median_params = tab.median_tab.sync_from_parent_geometry(
        "IRC 5 - Raised Kerb",
        median_geom,
        force=True,
        include_median=True,
    )
    railing_params = tab.railing_tab.sync_from_parent_geometry(
        "IRC 5 - RCC Railing",
        width_mm=300.0,
        height_m=1.1,
        force=True,
    )
    wearing_params = tab.wearing_course_tab.sync_from_parent_material("Concrete")
    tab.layout_tab.sync_from_bridge_context("None")
    crash_state_params = tab.crash_barrier_tab.sync_from_parent_state(force=False)
    median_state_params = tab.median_tab.sync_from_parent_state(include_median=True, force=False)
    railing_state_params = tab.railing_tab.sync_from_parent_state(force=False)
    wearing_state_params = tab.wearing_course_tab.sync_from_parent_state()

    assert "crash_barrier_type" in crash_params
    assert "median_present" in median_params
    assert "railing_type" in railing_params
    assert "wearing_course_material" in wearing_params
    assert tab.footpath_width.isEnabled() is False
    assert "crash_barrier_type" in crash_state_params
    assert "median_present" in median_state_params
    assert "railing_type" in railing_state_params
    assert "wearing_course_material" in wearing_state_params


def test_typical_section_validation_aggregates_lane_child_validation(qapp):
    tab = TypicalSectionDetailsTab()
    qapp.processEvents()

    tab.lane_details_tab.set_lane_rows(
        [{"lane_number": "1", "start": "1.00", "width": "3.00"}]
    )

    errors = tab.validate_tab()

    assert "Lane 1 width must be at least 3.50 m." in errors
    assert "Lane 1 start must be 0.00 m." in errors
