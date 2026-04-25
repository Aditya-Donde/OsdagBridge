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

    tab.layout_tab.clear_notices()
    assert tab.layout_tab.layout_notice_container.isHidden()
