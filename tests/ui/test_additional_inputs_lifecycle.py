import osdagbridge.desktop.ui.dialogs.additional_inputs as additional_inputs_module
from osdagbridge.core.utils.common import (
    KEY_BEARING_LENGTH,
    KEY_CROSS_BRACING_SECTION,
    KEY_CROSS_BRACING_SPACING,
    KEY_CROSS_BRACING_TYPE,
    KEY_DECK_REINF_SIZE,
    KEY_DECK_THICKNESS,
    KEY_END_DIAPHRAGM_SECTION,
    KEY_END_DIAPHRAGM_TYPE,
    KEY_FOOTPATH_PRESSURE_VALUE,
    KEY_GIRDER_IS_SECTION,
    KEY_GIRDER_TYPE,
    KEY_LONGITUDINAL_STIFFENER,
    KEY_SELF_WEIGHT_FACTOR,
    KEY_STIFFENER_DESIGN_METHOD,
)
from osdagbridge.desktop.ui.dialogs.additional_inputs import AdditionalInputs
from osdagbridge.desktop.ui.docks.input_dock import InputDock


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


def test_additional_inputs_save_accepts_and_exposes_values(qapp, monkeypatch):
    class DummyMessageBox:
        def __init__(self, *args, **kwargs):
            pass

        def exec(self):
            return "OK"

    monkeypatch.setattr(additional_inputs_module, "CustomMessageBox", DummyMessageBox)

    dialog = AdditionalInputs()
    qapp.processEvents()
    dialog.typical_section_tab.deck_thickness.setText("225")

    dialog._save_inputs()

    assert dialog.result() == AdditionalInputs.Accepted
    assert dialog.get_saved_data()[KEY_DECK_THICKNESS] == "225"
    assert dialog.get_all_values()[KEY_DECK_THICKNESS] == "225"


def test_additional_inputs_exports_and_restores_non_typical_keys(qapp):
    dialog = AdditionalInputs()
    qapp.processEvents()

    dialog._collect_all_values()

    assert dialog.saved_values["shear_stud_diameter"] == "20"
    assert dialog.saved_values["shear_stud_height"] == "100.00"
    assert dialog.saved_values["bearing_length"] == "400.00"
    assert dialog.saved_values[KEY_BEARING_LENGTH] == "400.00"
    assert dialog.saved_values["reinforcement_size"] == "12 mm"
    assert dialog.saved_values[KEY_DECK_REINF_SIZE] == "12 mm"

    dialog.set_properties_data({
        "shear_stud_diameter": "22",
        KEY_BEARING_LENGTH: "350.00",
        KEY_DECK_REINF_SIZE: "16 mm",
    })
    qapp.processEvents()

    assert dialog.design_options_tab.shear_stud_diameter_combo.currentText() == "22"
    assert dialog.support_tab.bearing_length_input.text() == "350.00"
    assert dialog.design_options_tab.reinforcement_size_combo.currentText() == "16 mm"


def test_member_properties_exports_common_keys_and_legacy_groups(qapp):
    dialog = AdditionalInputs()
    qapp.processEvents()

    dialog._collect_all_values()

    for key in (
        KEY_GIRDER_TYPE,
        KEY_GIRDER_IS_SECTION,
        KEY_STIFFENER_DESIGN_METHOD,
        KEY_LONGITUDINAL_STIFFENER,
        KEY_CROSS_BRACING_TYPE,
        KEY_CROSS_BRACING_SECTION,
        KEY_CROSS_BRACING_SPACING,
        KEY_END_DIAPHRAGM_TYPE,
        KEY_END_DIAPHRAGM_SECTION,
    ):
        assert key in dialog.saved_values

    for group in ("girder_details", "stiffener_details", "cross_bracing", "end_diaphragm"):
        assert isinstance(dialog.saved_values[group], dict)

    end_tab = dialog.section_properties_tab.end_diaphragm_tab
    assert dialog.saved_values[KEY_END_DIAPHRAGM_SECTION] == end_tab.cross_bracing_section_combo.currentText()


def test_member_properties_restores_common_and_nested_keys(qapp):
    dialog = AdditionalInputs()
    qapp.processEvents()

    dialog.set_properties_data({
        KEY_CROSS_BRACING_SPACING: "4.25",
        "end_diaphragm": {KEY_END_DIAPHRAGM_TYPE: "Rolled Beam"},
    })
    qapp.processEvents()

    section_tab = dialog.section_properties_tab
    assert section_tab.cross_bracing_tab.spacing_input.text() == "4.25"
    assert section_tab.end_diaphragm_tab.type_selector_combo.currentText() == "Rolled Beam"


def test_additional_inputs_reset_defaults_restores_loading_and_non_typical_defaults(qapp):
    dialog = AdditionalInputs()
    qapp.processEvents()

    live_tab = dialog.loading_tab.live_load_tab
    live_tab.footpath_mode_combo.setCurrentText("User-defined")
    live_tab.footpath_value_input.setText("7.50")
    dialog.support_tab.bearing_length_input.setText("350.00")
    dialog.design_options_tab.shear_stud_diameter_combo.setCurrentText("22")
    dialog.design_options_tab.reinforcement_size_combo.setCurrentText("16 mm")

    dialog.reset_defaults()
    qapp.processEvents()
    dialog._collect_all_values()

    assert live_tab.footpath_mode_combo.currentText() == "Automatic"
    assert live_tab.footpath_value_input.text() == "5.00"
    assert not live_tab.footpath_value_input.isEnabled()
    assert dialog.saved_values[KEY_FOOTPATH_PRESSURE_VALUE] == "5.00"
    assert dialog.support_tab.bearing_length_input.text() == "400.00"
    assert dialog.design_options_tab.shear_stud_diameter_combo.currentText() == "20"
    assert dialog.design_options_tab.reinforcement_size_combo.currentText() == "12 mm"


def test_additional_inputs_reset_button_scope_is_active_top_tab(qapp):
    dialog = AdditionalInputs()
    qapp.processEvents()

    dialog.support_tab.bearing_length_input.setText("350.00")
    dialog.design_options_tab.reinforcement_size_combo.setCurrentText("16 mm")
    dialog.tab_widget.setCurrentWidget(dialog.support_tab)

    dialog._apply_defaults()
    qapp.processEvents()

    assert dialog.support_tab.bearing_length_input.text() == "400.00"
    assert dialog.design_options_tab.reinforcement_size_combo.currentText() == "16 mm"


def test_additional_inputs_legacy_tabs_alias_and_label(qapp):
    dialog = AdditionalInputs()
    qapp.processEvents()

    assert dialog.tabs is dialog.tab_widget
    labels = [dialog.tabs.tabText(i) for i in range(dialog.tabs.count())]
    assert "Analysis/Design Options" in labels


def test_additional_inputs_apply_tab_visibility_controls_inner_tabs(qapp):
    dialog = AdditionalInputs()
    qapp.processEvents()

    inner_tabs = dialog.typical_section_tab.input_tabs
    railing_idx = dialog._find_inner_tab_index(inner_tabs, "Railing")
    median_idx = dialog._find_inner_tab_index(inner_tabs, "Median")

    dialog.apply_tab_visibility("None", "No")
    qapp.processEvents()

    assert not inner_tabs.isTabEnabled(railing_idx)
    assert not inner_tabs.isTabEnabled(median_idx)
    assert dialog.typical_section_tab.footpath_value == "None"
    assert not dialog.typical_section_tab.layout_tab.footpath_width.isEnabled()

    dialog.apply_tab_visibility("Both Sides", "Yes")
    qapp.processEvents()

    assert inner_tabs.isTabEnabled(railing_idx)
    assert inner_tabs.isTabEnabled(median_idx)
    assert dialog.footpath_value == "Both Sides"
    assert dialog.typical_section_tab.footpath_value == "Both Sides"
    assert dialog.typical_section_tab.layout_tab.footpath_width.isEnabled()


def test_additional_inputs_update_project_location_forwards_to_loading_tabs(qapp, monkeypatch):
    dialog = AdditionalInputs()
    qapp.processEvents()

    calls = []
    for attr in ("temperature_load_tab", "seismic_load_tab", "wind_load_tab"):
        tab = getattr(dialog.loading_tab, attr)
        monkeypatch.setattr(
            tab,
            "update_project_location",
            lambda data, name=attr: calls.append((name, data)),
        )

    location = {"city": "Pune"}
    dialog.update_project_location(location)

    assert calls == [
        ("temperature_load_tab", location),
        ("seismic_load_tab", location),
        ("wind_load_tab", location),
    ]


def test_input_dock_applies_additional_values_to_parent_input_dict(qapp, monkeypatch):
    class Backend:
        def input_values(self):
            return []

    class Parent:
        def __init__(self):
            self.input_dict = {}

        def common_design_func(self, trigger):
            self.trigger = trigger

    parent = Parent()
    dock = InputDock(backend=Backend(), parent=parent)
    monkeypatch.setattr(dock, "_run_cross_cutting_validation", lambda: None)

    dock._apply_additional_input_values({KEY_DECK_THICKNESS: "225"})

    assert dock.additional_input_values[KEY_DECK_THICKNESS] == "225"
    assert dock.get_all_input_values()[KEY_DECK_THICKNESS] == "225"
    assert parent.input_dict[KEY_DECK_THICKNESS] == "225"


def test_input_dock_save_dialog_updates_parent_input_dict(qapp, monkeypatch):
    class DummyMessageBox:
        def __init__(self, *args, **kwargs):
            pass

        def exec(self):
            return "OK"

    class Backend:
        def input_values(self):
            return []

    class Parent:
        def __init__(self):
            self.input_dict = {}

        def common_design_func(self, trigger):
            self.trigger = trigger

    def fake_exec(dialog):
        dialog.typical_section_tab.deck_thickness.setText("235")
        dialog.loading_tab.permanent_load_tab.self_weight_factor_input.setText("1.12")
        dialog.support_tab.bearing_length_input.setText("365.00")
        dialog.design_options_tab.reinforcement_size_combo.setCurrentText("16 mm")
        dialog._save_inputs()
        assert dialog.result() == AdditionalInputs.Accepted
        return dialog.result()

    monkeypatch.setattr(additional_inputs_module, "CustomMessageBox", DummyMessageBox)
    monkeypatch.setattr(AdditionalInputs, "exec_", fake_exec)

    parent = Parent()
    dock = InputDock(backend=Backend(), parent=parent)
    monkeypatch.setattr(dock, "_get_effective_carriageway_width", lambda: 7.5)
    monkeypatch.setattr(dock, "_run_cross_cutting_validation", lambda: None)

    dock._open_additional_inputs()

    assert dock.additional_input_values[KEY_DECK_THICKNESS] == "235"
    assert dock.additional_input_values[KEY_SELF_WEIGHT_FACTOR] == "1.12"
    assert dock.additional_input_values[KEY_BEARING_LENGTH] == "365.00"
    assert dock.additional_input_values[KEY_DECK_REINF_SIZE] == "16 mm"
    assert dock.additional_input_values[KEY_CROSS_BRACING_SPACING] == "3"
    assert dock.additional_input_values[KEY_GIRDER_TYPE] == "Welded"
    assert parent.input_dict[KEY_DECK_THICKNESS] == "235"
    assert parent.input_dict[KEY_SELF_WEIGHT_FACTOR] == "1.12"
    assert parent.input_dict[KEY_BEARING_LENGTH] == "365.00"
    assert parent.input_dict[KEY_DECK_REINF_SIZE] == "16 mm"
    assert parent.input_dict[KEY_CROSS_BRACING_SPACING] == "3"
    assert parent.input_dict[KEY_GIRDER_TYPE] == "Welded"
