"""Registry of schema-addressable CAD/preview widgets for UIBuilder."""

from osdagbridge.desktop.ui.dialogs.tabs.drawings.support_conditions_cad import SupportCADWidget
from osdagbridge.desktop.ui.dialogs.tabs.drawings.support_detail_cad import SupportDetailCADWidget
from osdagbridge.desktop.ui.docks.cad_cross_section import CrossSectionCADWidget
from osdagbridge.desktop.ui.utils.rolled_section_preview import RolledSectionPreview
from osdagbridge.desktop.ui.widgets.placeholder_section_preview import PlaceholderSectionPreviewWidget
from osdagbridge.desktop.ui.widgets.section_viewer import SectionPreviewWidget


CAD_WIDGETS = {
    "SupportCADWidget": SupportCADWidget,
    "SupportDetailCADWidget": SupportDetailCADWidget,
    "CrossSectionCADWidget": CrossSectionCADWidget,
    "RolledSectionPreview": RolledSectionPreview,
    "SectionPreviewWidget": SectionPreviewWidget,
    "PlaceholderSectionPreviewWidget": PlaceholderSectionPreviewWidget,
}
