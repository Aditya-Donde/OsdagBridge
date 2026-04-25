from osdagbridge.desktop.ui.dialogs.additional_inputs import AdditionalInputs


def test_additional_inputs_round_trip(qapp):
    dialog = AdditionalInputs()
    qapp.processEvents()

    snapshot = dialog.typical_section_tab.collect_data()
    snapshot.update(dialog.section_properties_tab.collect_data())
    snapshot.update(dialog.loading_tab.collect_data())
    snapshot.update(dialog.support_tab.collect_data())
    snapshot.update(dialog.design_options_tab.collect_data())
    snapshot.update(dialog.design_options_cont_tab.collect_data())

    assert isinstance(snapshot, dict)

    dialog.set_properties_data(snapshot)
    qapp.processEvents()

    dialog.reset_defaults()
    qapp.processEvents()

    errors = []
    for tab in (
        dialog.typical_section_tab,
        dialog.section_properties_tab,
        dialog.loading_tab,
        dialog.support_tab,
        dialog.design_options_tab,
        dialog.design_options_cont_tab,
    ):
        errors.extend(tab.validate_tab())

    assert isinstance(errors, list)
