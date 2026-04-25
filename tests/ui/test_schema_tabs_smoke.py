from osdagbridge.desktop.ui.dialogs.additional_inputs import AdditionalInputs
from osdagbridge.desktop.ui.dialogs.tabs.additional_inputs.loading_tab import LoadingTab
from osdagbridge.desktop.ui.dialogs.tabs.additional_inputs.section_properties_tab import SectionPropertiesTab
from osdagbridge.desktop.ui.dialogs.tabs.additional_inputs.support_conditions_tab import SupportConditionsTab
from osdagbridge.desktop.ui.dialogs.tabs.additional_inputs.design_options_tab import DesignOptionsTab
from osdagbridge.desktop.ui.dialogs.tabs.additional_inputs.design_options_cont_tab import DesignOptionsContTab
from osdagbridge.desktop.ui.dialogs.tabs.additional_inputs.tab_registry import _TAB_CLASSES, get_tab_class
from osdagbridge.desktop.ui.dialogs.tabs.additional_inputs.typical_section_details import TypicalSectionDetailsTab


def test_additional_inputs_dialog_builds(qapp):
    dialog = AdditionalInputs()
    qapp.processEvents()

    assert dialog.tab_widget.count() == 6
    assert dialog.typical_section_tab is not None
    assert dialog.section_properties_tab is not None
    assert dialog.loading_tab is not None


def test_top_level_tabs_build(qapp):
    widgets = [
        TypicalSectionDetailsTab(),
        SectionPropertiesTab(),
        LoadingTab(),
        SupportConditionsTab(),
        DesignOptionsTab(),
        DesignOptionsContTab(),
    ]
    qapp.processEvents()

    assert all(widget is not None for widget in widgets)
    assert all(widget.owner is widget for widget in widgets[3:])


def test_registered_tab_classes_import(qapp):
    imported = {name: get_tab_class(name) for name in _TAB_CLASSES}
    qapp.processEvents()

    assert set(imported) == set(_TAB_CLASSES)
