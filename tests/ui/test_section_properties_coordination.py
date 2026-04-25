from osdagbridge.desktop.ui.dialogs.tabs.section_properties_tab import SectionPropertiesTab


def test_section_properties_round_trip(qapp):
    tab = SectionPropertiesTab()
    qapp.processEvents()

    snapshot = tab.collect_data()
    assert isinstance(snapshot, dict)

    tab.restore_data(snapshot)
    qapp.processEvents()

    tab.reset_defaults()
    qapp.processEvents()

    errors = tab.validate_tab()
    assert isinstance(errors, list)


def test_girder_dependency_state_refreshes_dependents(qapp):
    tab = SectionPropertiesTab()
    qapp.processEvents()

    tab.set_girder_count(3)
    qapp.processEvents()

    state = tab.girder_details_tab.export_dependency_state()
    assert state["available_girders"] == ["G1", "G2", "G3"]

    tab.stiffener_details_tab.refresh_from_girder_state(state)
    tab.cross_bracing_tab.refresh_from_girder_state(state)
    tab.end_diaphragm_tab.refresh_from_girder_state(state)
    qapp.processEvents()

    pair_items = [
        tab.cross_bracing_tab.select_girders_combo.itemText(i)
        for i in range(tab.cross_bracing_tab.select_girders_combo.count())
    ]
    assert pair_items == ["G1 to G2", "G2 to G3"]
