from .girder_details import GIRDER_DETAILS_SCHEMA
from .stiffener_details import STIFFENER_DETAILS_SCHEMA
from .cross_bracing_details import CROSS_BRACING_DETAILS_SCHEMA
from .end_diaphragm_details import END_DIAPHRAGM_DETAILS_SCHEMA

MEMBER_PROPERTIES_SCHEMA_V1 = {
    "version": 1,
    "tabs": {
        "girder_details": {
            "id": "girder_details",
            "title": "Girder Details",
            "overview": GIRDER_DETAILS_SCHEMA.get("overview", []),
            "section_inputs": GIRDER_DETAILS_SCHEMA.get("section_inputs", []),
        },
        "stiffener_details": {
            "id": "stiffener_details",
            "title": "Stiffener Details",
            "overview": STIFFENER_DETAILS_SCHEMA.get("overview", []),
            "stiffener_inputs": STIFFENER_DETAILS_SCHEMA.get("stiffener_inputs", []),
            "web_buckling_inputs": STIFFENER_DETAILS_SCHEMA.get("web_buckling_inputs", []),
        },
        "cross_bracing_details": {
            "id": "cross_bracing_details",
            "title": "Cross-Bracing Details",
            "overview": CROSS_BRACING_DETAILS_SCHEMA.get("overview", []),
            "section_inputs": CROSS_BRACING_DETAILS_SCHEMA.get("section_inputs", []),
        },
        "end_diaphragm_details": {
            "id": "end_diaphragm_details",
            "title": "End Diaphragm Details",
            "views": END_DIAPHRAGM_DETAILS_SCHEMA.get("sections", []),
        },
    },
}
