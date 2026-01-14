"""
3D CAD Viewer Window for OsdagBridge.

- Embeds CustomViewer3d
- Calls CAD generator
"""

import sys

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout
)

from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB

# CAD generator
from osdagbridge.core.bridge_types.plate_girder.cad_generator import (
    PlateGirderCADGenerator
)

# Custom 3D Viewer
from osdagbridge.desktop.ui.utils.custom_3dviewer import CustomViewer3d


# MAIN WINDOW

class CAD3DWindow(QMainWindow):
    """
    Main 3D CAD window for OsdagBridge.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("OsdagBridge 3D CAD Viewer")
        self.resize(1200, 800)

        # CAD generator
        self.generator = PlateGirderCADGenerator()

        # UI setup
        self.setup_ui()
        self.setup_viewer()

        # Load initial CAD
        self.load_bridge()

    # UI SETUP

    def setup_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        self.layout = QVBoxLayout(central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)

    def setup_viewer(self):
        self.viewer = CustomViewer3d(self)
        self.viewer.setMouseTracking(True)

        # Initialize OCC driver
        self.viewer.InitDriver()

        self.viewer.context = self.viewer._display.Context
        self.viewer.view = self.viewer._display.View

        self.layout.addWidget(self.viewer)

    # CAD DISPLAY

    def load_bridge(self):
        """
        Generate and display bridge CAD.
        """
        cad_data = self.generator.generate()
        display = self.viewer._display

        if hasattr(self.viewer, "cleanup_for_new_model"):
            self.viewer.cleanup_for_new_model()
        display.EraseAll()

        # Colors
        GIRDER_COLOR = Quantity_Color(72/255, 72/255, 54/255, Quantity_TOC_RGB)
        STIFFENER_COLOR = Quantity_Color(30/255, 30/255, 30/255, Quantity_TOC_RGB)
        DECK_COLOR = Quantity_Color(180/255, 180/255, 180/255, Quantity_TOC_RGB)
        BARRIER_COLOR = Quantity_Color(120/255, 120/255, 120/255, Quantity_TOC_RGB)
        BRACING_COLOR = Quantity_Color(60/255, 60/255, 60/255, Quantity_TOC_RGB)

        # Girders
        for g in cad_data.get("girders", []):
            display.DisplayShape(g, color=GIRDER_COLOR, update=False)

        # Stiffeners
        for s in cad_data.get("stiffeners", []):
            display.DisplayShape(s, color=STIFFENER_COLOR, update=False)

        # Cross bracings
        for b in cad_data.get("cross_bracings", []):
            display.DisplayShape(b, color=BRACING_COLOR, update=False)

        # Deck
        display.DisplayShape(
            cad_data["deck_slab"],
            color=DECK_COLOR,
            update=False
        )
        # Deck textures
        for tex in cad_data.get("deck_textures", []):
            display.DisplayShape(
                tex,
                color=Quantity_Color(0.2,0.2,0.2, Quantity_TOC_RGB),
                update=False
            )

        # Crash barriers
        for cb in cad_data.get("crash_barriers", []):
            display.DisplayShape(cb, color=BARRIER_COLOR, update=False)

        # Median
        for mb in cad_data.get("median_barriers", []):
            display.DisplayShape(mb, color=BARRIER_COLOR, update=False)

        # Railings
        for r in cad_data.get("railings", []):
            display.DisplayShape(r, color=BARRIER_COLOR, update=False)

        # View setup (Osdag standard)
        display.View_Iso()
        display.FitAll()

        if hasattr(self.viewer, "display_view_cube"):
            self.viewer.display_view_cube()

    # REGENERATION

    def regenerate_bridge(self):
        """
        Regenerate CAD (used when parameters change).
        """
        self.load_bridge()


# ENTRY POINT

def main():
    app = QApplication(sys.argv)

    win = CAD3DWindow()
    win.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
