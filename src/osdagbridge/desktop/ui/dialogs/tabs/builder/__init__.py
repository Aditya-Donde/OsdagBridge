"""Schema-driven UI builder package.

The public API is the ``UIBuilder`` class. The two module constants
re-exported here are read by ``schema_io`` for value-collection logic.
"""

from osdagbridge.desktop.ui.dialogs.tabs.builder.constants import (
    _FIELD_AS_SECTION_TYPES,
    _SPECIAL_SECTION_TYPES,
)
from osdagbridge.desktop.ui.dialogs.tabs.builder.core import UIBuilder

__all__ = ["UIBuilder", "_FIELD_AS_SECTION_TYPES", "_SPECIAL_SECTION_TYPES"]
