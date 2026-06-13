from osdagbridge.desktop.ui.widgets.placeholder_section_preview import PlaceholderSectionPreviewWidget
from osdagbridge.desktop.ui.dialogs.additional_input.drawings.bracing_layout_cad import BracingLayoutCadWidget

class CrossBracingLayoutCad(BracingLayoutCadWidget):
    def __init__(self, parent=None):
        super().__init__(min_height=170, parent=parent)
        
class EndDiaphragmBracingLayoutCad(BracingLayoutCadWidget):
    def __init__(self, parent=None):
        super().__init__(min_height=170, parent=parent)


class BracingSectionPreview(PlaceholderSectionPreviewWidget):
    def __init__(self, parent=None):
        super().__init__("Bracing", 110, parent=parent)


class TopChordSectionPreview(PlaceholderSectionPreviewWidget):
    def __init__(self, parent=None):
        super().__init__("Top Chord", 110, parent=parent)


class BottomChordSectionPreview(PlaceholderSectionPreviewWidget):
    def __init__(self, parent=None):
        super().__init__("Bottom Chord", 110, parent=parent)