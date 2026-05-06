from osdagbridge.desktop.ui.dialogs.tabs.additional_inputs.section_properties_tab import SectionPropertiesTab


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
    assert tab.girder_details_tab.segment_table.rowCount() >= 1
    assert tab.girder_details_tab.girder_cad_view._selected_member_id == "G1M1"
    assert [segment["id"] for segment in tab.girder_details_tab.girder_cad_view._segments] == ["G1M1"]


def test_direct_girder_child_updates_dependents_via_parent_subscription(qapp):
    tab = SectionPropertiesTab()
    qapp.processEvents()

    tab.girder_details_tab.set_girder_count(3)
    qapp.processEvents()

    pair_items = [
        tab.cross_bracing_tab.select_girders_combo.itemText(i)
        for i in range(tab.cross_bracing_tab.select_girders_combo.count())
    ]
    assert pair_items == ["G1 to G2", "G2 to G3"]
    assert [
        tab.end_diaphragm_tab.select_girders_combo.itemText(i)
        for i in range(tab.end_diaphragm_tab.select_girders_combo.count())
    ] == ["G1 to G2", "G2 to G3"]


def test_leaving_girder_tab_commits_public_state_for_dependents(qapp):
    tab = SectionPropertiesTab()
    qapp.processEvents()

    tab.girder_details_tab.top_width_input.setText("450")
    qapp.processEvents()

    tab.section_tabs.setCurrentWidget(tab.stiffener_details_tab)
    qapp.processEvents()

    dims = tab.stiffener_details_tab._girder_state.get("section_dimensions_by_member", {})
    assert dims["G1M1"]["top_flange_width_mm"] == 450.0


def test_section_properties_design_mode_propagates_to_child_tabs(qapp):
    tab = SectionPropertiesTab()
    qapp.processEvents()

    tab.set_design_mode("customized")
    qapp.processEvents()

    assert tab.girder_details_tab.design_combo.currentText() == "Custom"
    assert tab.cross_bracing_tab.design_combo.currentText() == "Custom"
    assert tab.cross_bracing_tab.bracing_section_combo.isEnabled()
    assert tab.end_diaphragm_tab.cross_design_combo.currentText() == "Custom"
    assert tab.end_diaphragm_tab.rolled_design_combo.currentText() == "Custom"
    assert tab.end_diaphragm_tab.welded_design_combo.currentText() == "Custom"

    tab.set_design_mode("optimised")
    qapp.processEvents()

    assert tab.girder_details_tab.design_combo.currentText() == "Optimized"
    assert tab.cross_bracing_tab.design_combo.currentText() == "Optimized"
    assert not tab.cross_bracing_tab.bracing_section_combo.isEnabled()
    assert tab.end_diaphragm_tab.cross_design_combo.currentText() == "Optimized"
    assert tab.end_diaphragm_tab.rolled_design_combo.currentText() == "Optimized"
    assert tab.end_diaphragm_tab.welded_design_combo.currentText() == "Optimized"
