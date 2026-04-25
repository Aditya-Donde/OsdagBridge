"""Top-level tab configuration for the Additional Inputs dialog.

Each entry declares one top-level tab. The dialog reads this config to build
its tab bar; adding or reordering a top-level tab is a config edit, not a
dialog edit.
"""

from osdagbridge.desktop.ui.dialogs.tabs.additional_inputs.typical_section_details import TypicalSectionDetailsTab
from osdagbridge.desktop.ui.dialogs.tabs.additional_inputs.section_properties_tab import SectionPropertiesTab
from osdagbridge.desktop.ui.dialogs.tabs.additional_inputs.loading_tab import LoadingTab
from osdagbridge.desktop.ui.dialogs.tabs.additional_inputs.support_conditions_tab import SupportConditionsTab
from osdagbridge.desktop.ui.dialogs.tabs.additional_inputs.design_options_tab import DesignOptionsTab
from osdagbridge.desktop.ui.dialogs.tabs.additional_inputs.design_options_cont_tab import DesignOptionsContTab


def _typical_section_factory(dialog):
    return TypicalSectionDetailsTab(
        footpath_value=dialog.footpath_value,
        carriageway_width=dialog.carriageway_width,
        parent=dialog,
        initial_cad_state=dialog._initial_cad_state,
    )


ADDITIONAL_INPUTS_TAB_CONFIG = (
    {
        "id": "typical_section",
        "title": "Typical Section Details",
        "attr": "typical_section_tab",
        "factory": _typical_section_factory,
    },
    {
        "id": "section_properties",
        "title": "Member Properties",
        "attr": "section_properties_tab",
        "factory": lambda dialog: SectionPropertiesTab(parent=dialog),
    },
    {
        "id": "loading",
        "title": "Loading",
        "attr": "loading_tab",
        "factory": lambda dialog: LoadingTab(parent=dialog),
    },
    {
        "id": "support_conditions",
        "title": "Support Conditions",
        "attr": "support_tab",
        "factory": lambda dialog: SupportConditionsTab(parent_dialog=dialog),
    },
    {
        "id": "design_options",
        "title": "Design Options",
        "attr": "design_options_tab",
        "factory": lambda dialog: DesignOptionsTab(parent_dialog=dialog),
    },
    {
        "id": "design_options_cont",
        "title": "Design Options (Cont.)",
        "attr": "design_options_cont_tab",
        "factory": lambda dialog: DesignOptionsContTab(parent_dialog=dialog),
    },
)
