"""Backwards-compatibility shim.

The implementation moved into the ``builder/`` package; this module
re-exports the public surface so existing imports keep working.
"""

from osdagbridge.desktop.ui.dialogs.tabs.builder import (
    UIBuilder,
    _FIELD_AS_SECTION_TYPES,
    _SPECIAL_SECTION_TYPES,
)

__all__ = ["UIBuilder", "_FIELD_AS_SECTION_TYPES", "_SPECIAL_SECTION_TYPES"]
