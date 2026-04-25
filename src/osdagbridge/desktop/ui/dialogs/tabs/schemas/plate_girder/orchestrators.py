"""Orchestrator schemas for parent tab containers."""

ADDITIONAL_INPUTS_ORCHESTRATOR_SCHEMA = {
    "id": "additional_inputs_orchestrator",
    "sections": [
        {
            "id": "additional_inputs_tabs",
            "type": "tab_container",
            "tabs": [
                {"label": "Typical Section Details", "widget_class": "TypicalSectionDetailsTab", "bind": "typical_section_tab"},
                {"label": "Member Properties",       "widget_class": "SectionPropertiesTab",     "bind": "section_properties_tab"},
                {"label": "Loading",                 "widget_class": "LoadingTab",               "bind": "loading_tab"},
                {"label": "Support Conditions",      "widget_class": "SupportConditionsTab",     "bind": "support_tab"},
                {"label": "Design Options",          "widget_class": "DesignOptionsTab",         "bind": "design_options_tab"},
                {"label": "Design Options (Cont.)",  "widget_class": "DesignOptionsContTab",     "bind": "design_options_cont_tab"},
            ],
        }
    ],
}

TYPICAL_SECTION_ORCHESTRATOR_SCHEMA = {
    "id": "typical_section_orchestrator",
    "sections": [
        {
            "id": "cad_preview_group",
            "type": "cad",
            "widget": "CrossSectionCADWidget",
            "bind": "cad_preview",
            "min_height": 280,
            "max_height": 380,
            "scrollable": True,
            "properties": {"scale_factor": 0.65},
        },
        {
            "id": "typical_section_tabs",
            "type": "tab_container",
            "tabs": [
                {"label": "Layout", "widget_class": "LayoutTab", "bind": "layout_tab"},
                {"label": "Crash Barrier", "widget_class": "CrashBarrierTab", "bind": "crash_barrier_tab"},
                {"label": "Railing", "widget_class": "RailingTab", "bind": "railing_tab"},
                {"label": "Median", "widget_class": "MedianTab", "bind": "median_tab"},
                {"label": "Wearing Course", "widget_class": "WearingCourseTab", "bind": "wearing_course_tab"},
                {"label": "Lane Details", "widget_class": "LaneDetailsTab", "bind": "lane_details_tab"},
            ]
        }
    ]
}

LOADING_ORCHESTRATOR_SCHEMA = {
    "id": "loading_orchestrator",
    "sections": [
        {
            "id": "loading_tabs",
            "type": "tab_container",
            "tabs": [
                {"label": "Permanent Load", "widget_class": "PermanentLoadTab", "bind": "permanent_load_tab"},
                {"label": "Live Load", "widget_class": "LiveLoadTab", "bind": "live_load_tab"},
                {"label": "Seismic Load", "widget_class": "SeismicLoadTab", "bind": "seismic_load_tab"},
                {"label": "Wind Load", "widget_class": "WindLoadTab", "bind": "wind_load_tab"},
                {"label": "Temperature Load", "widget_class": "TemperatureLoadTab", "bind": "temperature_load_tab"},
                {"label": "Custom Load", "widget_class": "CustomLoadTab", "bind": "custom_load_tab"},
                {"label": "Load Combination", "widget_class": "LoadCombinationTab", "bind": "load_combination_tab"},
            ]
        }
    ]
}

SECTION_PROPERTIES_ORCHESTRATOR_SCHEMA = {
    "id": "section_properties_orchestrator",
    "sections": [
        {
            "id": "section_properties_tabs",
            "type": "tab_container",
            "tabs": [
                {"label": "Girder Details", "widget_class": "GirderDetailsTab", "bind": "girder_details_tab"},
                {"label": "Stiffener Details", "widget_class": "StiffenerDetailsTab", "bind": "stiffener_details_tab"},
                {"label": "Cross-Bracing Details", "widget_class": "CrossBracingDetailsTab", "bind": "cross_bracing_tab"},
                {"label": "End Diaphragm Details", "widget_class": "EndDiaphragmDetailsTab", "bind": "end_diaphragm_tab"},
            ]
        }
    ]
}
