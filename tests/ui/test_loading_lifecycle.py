from osdagbridge.desktop.ui.dialogs.tabs.loading_tab import LoadingTab


def test_loading_tab_round_trip(qapp):
    tab = LoadingTab()
    qapp.processEvents()

    data = tab.collect_data()
    assert isinstance(data, dict)
    assert tab.live_load_tab is not None
    assert tab.custom_load_tab is not None
    assert tab.load_combination_tab is not None

    tab.restore_data(data)
    qapp.processEvents()

    tab.reset_defaults()
    qapp.processEvents()

    errors = tab.validate_tab()
    assert isinstance(errors, list)


def test_loading_tab_uses_child_lifecycle_only(qapp):
    tab = LoadingTab()
    qapp.processEvents()

    child_data = {}
    for child in (
        tab.permanent_load_tab,
        tab.live_load_tab,
        tab.seismic_load_tab,
        tab.wind_load_tab,
        tab.temperature_load_tab,
        tab.custom_load_tab,
        tab.load_combination_tab,
    ):
        child_data.update(child.collect_data())

    assert tab.collect_data() == child_data
