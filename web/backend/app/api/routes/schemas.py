from fastapi import APIRouter

from osdagbridge.core.bridge_types.plate_girder.ui_fields_additional_input import (
    LAYOUT_TAB_SCHEMA,
    CRASH_BARRIER_TAB_SCHEMA,
    MEDIAN_TAB_SCHEMA,
    RAILING_TAB_SCHEMA,
    WEARING_COURSE_TAB_SCHEMA,
    LANE_DETAILS_TAB_SCHEMA,
    PERMANENT_LOAD_TAB_SCHEMA,
    LIVE_LOAD_TAB_SCHEMA,
    SEISMIC_LOAD_TAB_SCHEMA,
    WIND_LOAD_TAB_SCHEMA,
    TEMPERATURE_LOAD_TAB_SCHEMA,
    CUSTOM_LOAD_TAB_SCHEMA,
    LOAD_COMBINATION_TAB_SCHEMA,
    SUPPORT_CONDITIONS_SCHEMA,
    DESIGN_OPTIONS_SCHEMA,
    DESIGN_OPTIONS_CONT_SCHEMA,
    GIRDER_DETAILS_SCHEMA,
    STIFFENER_DETAILS_SCHEMA,
    CROSS_BRACING_DETAILS_SCHEMA,
    END_DIAPHRAGM_DETAILS_SCHEMA,
    MEMBER_PROPERTIES_SCHEMA_V1
)

router = APIRouter(prefix="/schemas", tags=["Schemas"])

@router.get("/")
def get_all_schemas():
    """
    Returns all UI schemas required by the Additional Inputs dialog.
    The frontend uses these to dynamically render forms.
    """
    return {
        "layout_tab": LAYOUT_TAB_SCHEMA,
        "crash_barrier_tab": CRASH_BARRIER_TAB_SCHEMA,
        "median_tab": MEDIAN_TAB_SCHEMA,
        "railing_tab": RAILING_TAB_SCHEMA,
        "wearing_course_tab": WEARING_COURSE_TAB_SCHEMA,
        "lane_details_tab": LANE_DETAILS_TAB_SCHEMA,
        "permanent_load_tab": PERMANENT_LOAD_TAB_SCHEMA,
        "live_load_tab": LIVE_LOAD_TAB_SCHEMA,
        "seismic_load_tab": SEISMIC_LOAD_TAB_SCHEMA,
        "wind_load_tab": WIND_LOAD_TAB_SCHEMA,
        "temperature_load_tab": TEMPERATURE_LOAD_TAB_SCHEMA,
        "custom_load_tab": CUSTOM_LOAD_TAB_SCHEMA,
        "load_combination_tab": LOAD_COMBINATION_TAB_SCHEMA,
        "support_conditions_tab": SUPPORT_CONDITIONS_SCHEMA,
        "design_options_tab": DESIGN_OPTIONS_SCHEMA,
        "design_options_cont_tab": DESIGN_OPTIONS_CONT_SCHEMA,
        "girder_details": GIRDER_DETAILS_SCHEMA,
        "stiffener_details": STIFFENER_DETAILS_SCHEMA,
        "cross_bracing_details": CROSS_BRACING_DETAILS_SCHEMA,
        "end_diaphragm_details": END_DIAPHRAGM_DETAILS_SCHEMA,
        "member_properties_v1": MEMBER_PROPERTIES_SCHEMA_V1,
    }
