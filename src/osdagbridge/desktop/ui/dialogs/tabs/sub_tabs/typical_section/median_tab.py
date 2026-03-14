"""Median sub-tab — fully schema-driven via GeneralizedSchemaSubTab."""
from osdagbridge.core.bridge_types.plate_girder.ui_fields_additional_input import MEDIAN_TAB_SCHEMA
from osdagbridge.desktop.ui.dialogs.tabs.generalized_schema_tab import GeneralizedSchemaSubTab


class MedianTab(GeneralizedSchemaSubTab):
    """Constructs the Median tab from its schema definition.

    Label references for visibility callbacks (``median_density_label``,
    ``median_area_label``, ``median_post_spacing_label``) are bound onto
    the *owner* via the ``label_bind`` schema key, making them available
    to ``on_median_type_changed`` on the owner.
    """

    def __init__(self, owner):
        super().__init__(MEDIAN_TAB_SCHEMA, owner=owner, parent=owner)
