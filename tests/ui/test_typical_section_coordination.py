from osdagbridge.desktop.ui.dialogs.tabs.typical_section_details import TypicalSectionDetailsTab


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


def test_typical_section_subtab_state_exports(qapp):
    tab = TypicalSectionDetailsTab()
    qapp.processEvents()

    assert isinstance(tab.crash_barrier_tab.export_barrier_state(), dict)
    assert isinstance(tab.median_tab.export_median_state(include_median=True), dict)
    assert isinstance(tab.railing_tab.export_railing_state(), dict)
    assert isinstance(tab.wearing_course_tab.export_wearing_state(), dict)
