"""Crash Barrier sub-tab — fully schema-driven via GeneralizedSchemaSubTab."""
from osdagbridge.core.bridge_types.plate_girder.ui_fields_additional_input import CRASH_BARRIER_TAB_SCHEMA
from osdagbridge.desktop.ui.dialogs.tabs.generalized_schema_tab import GeneralizedSchemaSubTab


class CrashBarrierTab(GeneralizedSchemaSubTab):
    """Constructs the Crash Barrier tab from its schema definition.

    Label references for visibility callbacks (``crash_barrier_density_label``,
    ``crash_barrier_area_label``, ``crash_barrier_post_spacing_label``) are
    bound onto the *owner* via the ``label_bind`` schema key, making them
    available to ``on_crash_barrier_type_changed`` on the owner.
    """

    def __init__(self, owner):
        super().__init__(CRASH_BARRIER_TAB_SCHEMA, owner=owner, parent=owner)
