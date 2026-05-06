import osdagbridge.desktop.ui.dialogs.tabs.additional_inputs.sub_tabs.loading.custom_load_tab as custom_load_tab_module

from osdagbridge.desktop.ui.dialogs.tabs.additional_inputs.loading_tab import LoadingTab
from osdagbridge.desktop.ui.dialogs.tabs.additional_inputs.sub_tabs.loading.load_combo_dialog import (
    LoadComboDialog,
)


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


def test_loading_project_location_updates_saved_wind_and_temperature(qapp):
    tab = LoadingTab()
    qapp.processEvents()

    tab.wind_load_tab.update_project_location({"weather_data": {"wind_speed": 44}})
    tab.temperature_load_tab.update_project_location({"weather_data": {"max_temp": 48, "min_temp": 6}})
    qapp.processEvents()

    data = tab.collect_data()

    assert tab.wind_load_tab.basic_wind_speed_input.text() == "44"
    assert tab.temperature_load_tab.highest_max_temp_input.text() == "48"
    assert tab.temperature_load_tab.lowest_min_temp_input.text() == "6"
    assert data["basic_wind_speed"] == "44"
    assert data["highest_max_temp"] == "48"
    assert data["lowest_min_temp"] == "6"


def test_loading_reset_restores_seismic_combo_default(qapp):
    tab = LoadingTab()
    qapp.processEvents()

    seismic = tab.seismic_load_tab
    seismic.soil_type_combo.setCurrentText("Type III – Soft Soil")

    tab.reset_defaults()
    qapp.processEvents()

    assert seismic.soil_type_combo.currentText() == "Type I – Rocky or Hard"


def test_loading_restores_multiple_live_custom_vehicles(qapp):
    tab = LoadingTab()
    qapp.processEvents()

    tab.live_load_tab._add_custom_vehicle({"name": "Truck 1"})
    tab.live_load_tab._add_custom_vehicle({"name": "Truck 2"})
    data = tab.collect_data()

    restored = LoadingTab()
    qapp.processEvents()
    restored.restore_data(data)
    qapp.processEvents()

    assert set(restored.live_load_tab.custom_vehicles) == {"Truck 1", "Truck 2"}
    assert restored.live_load_tab.custom_vehicle_table.rowCount() == 2


def test_loading_custom_load_cases_are_available_to_combinations(qapp):
    tab = LoadingTab()
    qapp.processEvents()

    tab.custom_load_tab.custom_load_items.append({
        "load_case": "Custom",
        "custom_load_case_name": "SPECIAL",
        "load_type": "Point",
        "point_left": "1.0",
        "point_bearing": "0.0",
    })
    tab.custom_load_tab._sync_owner_items()

    choices = LoadComboDialog._build_load_case_choices(tab.load_combination_tab)

    assert "SPECIAL" in choices


def test_loading_custom_load_line_and_area_widgets_are_distinct(qapp):
    tab = LoadingTab()
    qapp.processEvents()

    custom = tab.custom_load_tab

    assert custom.custom_line_left_start is not custom.custom_area_left_start
    assert custom.custom_line_left_end is not custom.custom_area_left_end
    assert custom.custom_line_bearing_start is not custom.custom_area_bearing_start
    assert custom.custom_line_bearing_end is not custom.custom_area_bearing_end

    custom.custom_line_left_start.setText("1.0")
    custom.custom_area_left_start.setText("2.0")

    assert custom.custom_line_left_start.text() == "1.0"
    assert custom.custom_area_left_start.text() == "2.0"


def test_loading_custom_load_collects_only_persisted_rows(qapp):
    tab = LoadingTab()
    qapp.processEvents()

    custom = tab.custom_load_tab
    custom.custom_load_type_combo.setCurrentText("Area")
    custom.custom_area_left_start.setText("99.0")
    custom.custom_load_items.append({
        "load_case": "DL",
        "load_type": "Point",
        "point_left": "1.0",
        "point_bearing": "0.0",
    })

    data = custom.collect_data()

    assert data == {"loading.custom_load_items": custom.custom_load_items}
    assert "custom_area_left_start" not in data
    assert "custom_load_type" not in data


def test_loading_custom_load_area_save_uses_area_widgets_and_legacy_keys(qapp, monkeypatch):
    class DummyMessageBox:
        def __init__(self, *args, **kwargs):
            pass

        def exec(self):
            return "OK"

    monkeypatch.setattr(custom_load_tab_module, "CustomMessageBox", DummyMessageBox)

    tab = LoadingTab()
    qapp.processEvents()

    custom = tab.custom_load_tab
    custom.custom_load_type_combo.setCurrentText("Area")
    custom.custom_line_left_start.setText("1.0")
    custom.custom_line_left_end.setText("2.0")
    custom.custom_line_bearing_start.setText("3.0")
    custom.custom_line_bearing_end.setText("4.0")
    custom.custom_area_left_start.setText("10.0")
    custom.custom_area_left_end.setText("20.0")
    custom.custom_area_bearing_start.setText("30.0")
    custom.custom_area_bearing_end.setText("40.0")

    custom._on_save_custom_load()
    qapp.processEvents()

    saved = custom.custom_load_items[-1]
    assert saved["load_type"] == "Area"
    assert saved["line_left_start"] == "10.0"
    assert saved["line_left_end"] == "20.0"
    assert saved["line_bearing_start"] == "30.0"
    assert saved["line_bearing_end"] == "40.0"
    assert custom.custom_load_table.item(0, 2).text() == "10.0 - 20.0"
    assert custom.custom_load_table.item(0, 3).text() == "30.0 - 40.0"
    assert custom.custom_line_left_start.text() == ""
    assert custom.custom_area_left_start.text() == ""


def test_loading_custom_load_edit_populates_area_widgets(qapp):
    tab = LoadingTab()
    qapp.processEvents()

    custom = tab.custom_load_tab
    custom._apply_saved_range_values({
        "line_left_start": "5.0",
        "line_left_end": "7.5",
        "line_bearing_start": "-1.5",
        "line_bearing_end": "1.5",
    })

    assert custom.custom_area_left_start.text() == "5.0"
    assert custom.custom_area_left_end.text() == "7.5"
    assert custom.custom_area_bearing_start.text() == "-1.5"
    assert custom.custom_area_bearing_end.text() == "1.5"
    assert custom.custom_line_left_start.text() == "5.0"
    assert custom.custom_line_left_end.text() == "7.5"


def test_loading_restore_accepts_legacy_prefixed_widget_keys(qapp):
    tab = LoadingTab()
    qapp.processEvents()

    tab.restore_data({"live_load_tab.eccentricity_input": "1.25"})
    qapp.processEvents()

    assert tab.live_load_tab.eccentricity_input.text() == "1.25"
