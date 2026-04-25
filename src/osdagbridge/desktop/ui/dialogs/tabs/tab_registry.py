"""Registry of tab classes for UIBuilder dynamic instantiation."""

from typing import Type, Dict
import importlib

# Map of class name to its full module path
_TAB_CLASSES = {
    # Typical Section
    "LayoutTab": "osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.typical_section.layout_tab.LayoutTab",
    "CrashBarrierTab": "osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.typical_section.crash_barrier_tab.CrashBarrierTab",
    "MedianTab": "osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.typical_section.median_tab.MedianTab",
    "RailingTab": "osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.typical_section.railing_tab.RailingTab",
    "WearingCourseTab": "osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.typical_section.wearing_course_tab.WearingCourseTab",
    "LaneDetailsTab": "osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.typical_section.lane_details_tab.LaneDetailsTab",

    # Loading
    "PermanentLoadTab": "osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.loading.permanent_load_tab.PermanentLoadTab",
    "LiveLoadTab": "osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.loading.live_load_tab.LiveLoadTab",
    "SeismicLoadTab": "osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.loading.seismic_load_tab.SeismicLoadTab",
    "WindLoadTab": "osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.loading.wind_load_tab.WindLoadTab",
    "TemperatureLoadTab": "osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.loading.temperature_load_tab.TemperatureLoadTab",
    "CustomLoadTab": "osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.loading.custom_load_tab.CustomLoadTab",
    "LoadCombinationTab": "osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.loading.load_combination_tab.LoadCombinationTab",

    # Section Properties
    "GirderDetailsTab": "osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.section_properties.girder_details_tab.GirderDetailsTab",
    "StiffenerDetailsTab": "osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.section_properties.stiffener_details_tab.StiffenerDetailsTab",
    "CrossBracingDetailsTab": "osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.section_properties.cross_bracing_details_tab.CrossBracingDetailsTab",
    "EndDiaphragmDetailsTab": "osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.section_properties.end_diaphragm_details_tab.EndDiaphragmDetailsTab",
}

def get_tab_class(class_name: str) -> Type:
    """Lazily load and return the tab class by name."""
    if class_name not in _TAB_CLASSES:
        raise ValueError(f"Tab class '{class_name}' not found in registry.")
    
    module_path, attr_name = _TAB_CLASSES[class_name].rsplit(".", 1)
    module = importlib.import_module(module_path)
    return getattr(module, attr_name)
