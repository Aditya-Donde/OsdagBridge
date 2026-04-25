from osdagbridge.desktop.ui.dialogs.additional_inputs import AdditionalInputs
from osdagbridge.desktop.ui.dialogs.tabs.loading_tab import LoadingTab
from osdagbridge.desktop.ui.dialogs.tabs.section_properties_tab import SectionPropertiesTab
from osdagbridge.desktop.ui.dialogs.tabs.support_conditions_tab import SupportConditionsTab
from osdagbridge.desktop.ui.dialogs.tabs.design_options_tab import DesignOptionsTab
from osdagbridge.desktop.ui.dialogs.tabs.design_options_cont_tab import DesignOptionsContTab
from osdagbridge.desktop.ui.dialogs.tabs.tab_registry import _TAB_CLASSES, get_tab_class
from osdagbridge.desktop.ui.dialogs.tabs.typical_section_details import TypicalSectionDetailsTab


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
        SupportConditionsTab(parent_dialog=None),
        DesignOptionsTab(parent_dialog=None),
        DesignOptionsContTab(parent_dialog=None),
    ]
    qapp.processEvents()

    assert all(widget is not None for widget in widgets)


def test_registered_tab_classes_import(qapp):
    imported = {name: get_tab_class(name) for name in _TAB_CLASSES}
    qapp.processEvents()

    assert set(imported) == set(_TAB_CLASSES)
