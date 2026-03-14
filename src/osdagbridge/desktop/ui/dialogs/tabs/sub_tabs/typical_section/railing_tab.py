"""Railing sub-tab — fully schema-driven via GeneralizedSchemaSubTab."""
from osdagbridge.core.bridge_types.plate_girder.ui_fields_additional_input import RAILING_TAB_SCHEMA
from osdagbridge.desktop.ui.dialogs.tabs.generalized_schema_tab import GeneralizedSchemaSubTab


class RailingTab(GeneralizedSchemaSubTab):
    """Constructs the Railing tab from its schema definition.

    All field creation, binding, and callback wiring is handled by the
    parent class.  Business-logic callbacks live on the *owner*
    (TypicalSectionDetailsTab) and are wired via the schema's
    ``on_change`` / ``on_editing_finished`` keys.
    """

    def __init__(self, owner):
        super().__init__(RAILING_TAB_SCHEMA, owner=owner, parent=owner)
