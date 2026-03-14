"""
3D CAD Viewer Window for OsdagBridge.

- Embeds CustomViewer3d
- Calls CAD generator
- Multi-select component visibility
"""

import sys

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QCheckBox,
    QPushButton
)
from PySide6.QtCore import QTimer, Qt

from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCC.Display.backend import load_backend

# CAD generator
from osdagbridge.core.bridge_types.plate_girder.cad_generator import (
    PlateGirderCADGenerator
)

# Custom 3D Viewer 
from osdagbridge.desktop.ui.utils.custom_3dviewer import CustomViewer3d


class CAD3DWindow(QWidget):
    """
    Main 3D CAD window for OsdagBridge.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("OsdagBridge 3D CAD Viewer")
        self.resize(1200, 800)

        # CAD generator
        self.generator = PlateGirderCADGenerator()

        self.generator.model_data = self.generator.generate()

        # Internal CAD state
        self.viewer = None
        self.display = None
        self._cad_init_pending = True

        # UI + CAD setup
        self.setup_ui()
        self.init_display()

    # UI SETUP 

    def setup_ui(self):

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Component selector 
        self.component_selector = BridgeComponentCheckbox(self)
        self.component_selector.hide()
        self.layout.addWidget(self.component_selector)


    # CAD INITIALIZATION 

    def init_display(self):
        """
        CAD initialization.

        - Creates CustomViewer3d
        - Defers InitDriver for safety
        """

        load_backend("pyside6")

        self.viewer = CustomViewer3d(self)
        self.viewer.setMouseTracking(True)
        self.layout.addWidget(self.viewer)

        QTimer.singleShot(0, self._deferred_init_driver)

    def _deferred_init_driver(self):
        if not self._cad_init_pending:
            return

        self.viewer.InitDriver()
        self._cad_init_pending = False

        self._complete_cad_init()
        self.load_bridge()

    def _complete_cad_init(self):
        """
        Complete CAD setup after InitDriver.
        REQUIRED for hover, selection, view cube.
        """

        self.display = self.viewer._display

        self.viewer.context = self.display.Context
        self.viewer.view = self.display.View

        self.viewer.context.SetAutomaticHilight(False)

        if hasattr(self.viewer, "display_view_cube"):
            self.viewer.display_view_cube()

        # ADD ZOOM BUTTONS
        self.create_cad_view_controls()

    def _is_display_ready(self):
        return self.display is not None and not self._cad_init_pending

    # CAD DISPLAY 
    def load_bridge(self):
        if not self._is_display_ready():
            return

        cad_data = self.generator.model_data
        display = self.display
        context = self.viewer.context

        if hasattr(self.viewer, "cleanup_for_new_model"):
            self.viewer.cleanup_for_new_model()
        display.EraseAll()

        # COLORS 
        WEB_COLOR = Quantity_Color(47/255.0, 47/255.0, 35/255.0, Quantity_TOC_RGB)
        FLANGE_COLOR = Quantity_Color(134/255.0, 134/255.0, 100/255.0, Quantity_TOC_RGB)
        STIFFENER_COLOR = Quantity_Color(72/255, 72/255, 54/255, Quantity_TOC_RGB)
        DECK_COLOR = Quantity_Color(100/255, 100/255, 100/255, Quantity_TOC_RGB)
        BARRIER_COLOR = Quantity_Color(40/255, 40/255, 40/255, Quantity_TOC_RGB)  #Quantity_Color(120/255, 120/255, 120/255, Quantity_TOC_RGB)
        BRACING_COLOR = Quantity_Color(60/255, 60/255, 60/255, Quantity_TOC_RGB)
        WBEAM_COLOR = Quantity_Color(128/255, 128/255, 128/255, Quantity_TOC_RGB)
        BARRIER_POST_COLOR = Quantity_Color(20/255, 20/255, 20/255, Quantity_TOC_RGB)
        SUPPORT_COLOR = Quantity_Color(20/255.0, 20/255.0, 20/255.0, Quantity_TOC_RGB)



        # HELPER 
        def display_and_register(shapes, key, label, color, transparency=None):
            if not shapes:
                return

            if not isinstance(shapes, list):
                shapes = [shapes]

            ais_list = []

            for shp in shapes:
                ais = display.DisplayShape(shp, color=color, transparency=transparency, update=False)
                ais = ais[0] if isinstance(ais, list) else ais

                context.Activate(ais, 0)   # REQUIRED for hover
                ais_list.append(ais)

            self.viewer.model_ais_objects[key] = ais_list
            self.viewer.model_hover_labels[key] = label

      

        self.viewer.model_ais_objects = {}

        #  PLATE GIRDER (WEB + FLANGES SEPARATE COLORS) 

        display_and_register(
            cad_data.get("girder_web", []),
            "Girder Web",
            "Girder Web",
            WEB_COLOR
        )

        display_and_register(
            cad_data.get("girder_flanges", []),
            "Girder Flange",
            "Girder Flange",
            FLANGE_COLOR
        )


        display_and_register(
            cad_data.get("stiffeners", []),
            "Stiffener",
            "Stiffener",
            STIFFENER_COLOR
        )

        display_and_register(
            cad_data.get("supports", []),
            "Support",
            "Support",
            SUPPORT_COLOR,
            transparency=0.6
        )


        display_and_register(
            cad_data.get("cross_bracings", []),
            "Cross Bracing",
            "Cross Bracing",
            BRACING_COLOR
        )

        display_and_register(
            cad_data.get("deck_slab"),
            "Deck",
            "Deck Slab",
            DECK_COLOR
        )
        # DECK TEXTURES (DISPLAY ONLY, NO HOVER)
        self.viewer.deck_texture_ais = []

        for tex in cad_data.get("deck_textures", []):
            ais = display.DisplayShape(
                tex,
                color=Quantity_Color(0.2, 0.2, 0.2, Quantity_TOC_RGB),
                update=False
            )
            ais = ais[0] if isinstance(ais, list) else ais
            self.viewer.deck_texture_ais.append(ais)



        display_and_register(
            cad_data.get("crash_barrier_w_beams", []),
            "Crash Barrier W-Beam",
            "W-Beam",
            WBEAM_COLOR
        )

        
        display_and_register(
            cad_data.get("median_w_beams", []),
            "Median W-Beam",
            "Median W-Beam",
            WBEAM_COLOR
        )

        display_and_register(
            cad_data.get("crash_barriers", []),
            "Crash Barrier",
            "Crash Barrier",
            BARRIER_POST_COLOR
        )


        display_and_register(
            cad_data.get("median_barriers", []),
            "Median",
            "Median Barrier",
            BARRIER_COLOR
        )

        display_and_register(
            cad_data.get("railings", []),
            "Railing",
            "Railing",
            BARRIER_COLOR
        )

        # FINAL VIEW 
        display.View_Iso()
        display.FitAll()

        if hasattr(self.viewer, "display_view_cube"):
            self.viewer.display_view_cube()


        self.component_selector.show()

    # ZOOM CONTROLS 

    def create_cad_view_controls(self):
        """Create zoom buttons below the view cube."""

        self._view_cube_size = 75
        self._view_cube_margin = 10
        self._zoom_btn_size = 40
        self._zoom_spacing = 6

        self.zoom_in_btn = QPushButton("+", self.viewer)
        self.zoom_in_btn.setFixedSize(self._zoom_btn_size, self._zoom_btn_size)
        self.zoom_in_btn.setCursor(Qt.PointingHandCursor)
        self.zoom_in_btn.clicked.connect(lambda: self.display.ZoomFactor(1.1))
        self._style_zoom_button(self.zoom_in_btn)

        self.zoom_out_btn = QPushButton("-", self.viewer)
        self.zoom_out_btn.setFixedSize(self._zoom_btn_size, self._zoom_btn_size)
        self.zoom_out_btn.setCursor(Qt.PointingHandCursor)
        self.zoom_out_btn.clicked.connect(lambda: self.display.ZoomFactor(1 / 1.1))
        self._style_zoom_button(self.zoom_out_btn)

        self.zoom_in_btn.show()
        self.zoom_out_btn.show()

        self.position_zoom_buttons()

        self._orig_resize_event = self.viewer.resizeEvent
        self.viewer.resizeEvent = self._cad_resize_proxy

    def _style_zoom_button(self, btn):
        btn.setStyleSheet("""
            QPushButton {
                font-size: 20px;
                font-weight: bold;
                background-color: white;
                border: 1px solid #bdbdbd;
            }
            QPushButton:hover {
                background-color: #e6e6e6;
            }
            QPushButton:pressed {
                background-color: #d6d6d6;
            }
        """)

    def position_zoom_buttons(self):
        if not hasattr(self, "zoom_in_btn"):
            return

        w = self.viewer.width()

        cube_right = w - self._view_cube_margin
        cube_left = cube_right - self._view_cube_size

        cube_bottom = self._view_cube_margin + self._view_cube_size + 30

        center_x = cube_left + self._view_cube_size // 2
        btn_x = center_x - self._zoom_btn_size // 2

        btn_y_1 = cube_bottom + self._zoom_spacing
        btn_y_2 = btn_y_1 + self._zoom_btn_size + self._zoom_spacing

        self.zoom_in_btn.move(btn_x, btn_y_1)
        self.zoom_out_btn.move(btn_x, btn_y_2)

    def _cad_resize_proxy(self, event):
        if self._orig_resize_event:
            self._orig_resize_event(event)
        self.position_zoom_buttons()

    def show_full_model(self):
        """
        Display all bridge components 
        """
        if not self._is_display_ready():
            return

        context = self.viewer.context

        # Show all structural components
        for ais_list in self.viewer.model_ais_objects.values():
            for ais in ais_list:
                context.Display(ais, False)

        # Show deck textures
        for ais in getattr(self.viewer, "deck_texture_ais", []):
            context.Display(ais, False)

        self.display.FitAll()
        self.display.Repaint()


    def update_component_visibility(self, selected_components):
        """
        Show/hide components based on multi-selection.
        
        Args:
            selected_components: List of component keys that should be visible
        """
        if not self._is_display_ready():
            return

        context = self.viewer.context

        # Component key mappings (handles composite components)
        component_map = {
            "Crash Barrier": ["Crash Barrier", "Crash Barrier W-Beam"],
            "Median": ["Median", "Median W-Beam"],
            "Girder": ["Girder Web", "Girder Flange", "Support", "Stiffener"],
            "Deck": ["Deck"],
            "Cross Bracing": ["Cross Bracing"],
            "Railing": ["Railing"],
            "Stiffener": ["Stiffener"]
        }

        # Collect all keys that should be visible
        visible_keys = set()
        for comp in selected_components:
            if comp in component_map:
                visible_keys.update(component_map[comp])

        # Update visibility for all structural components
        for key, ais_list in self.viewer.model_ais_objects.items():
            should_show = key in visible_keys
            for ais in ais_list:
                if should_show:
                    context.Display(ais, False)
                else:
                    context.Erase(ais, False)

        # Handle deck textures (show only if Deck is selected)
        show_deck_textures = "Deck" in selected_components
        for ais in getattr(self.viewer, "deck_texture_ais", []):
            if show_deck_textures:
                context.Display(ais, False)
            else:
                context.Erase(ais, False)

        self.display.FitAll()
        self.display.Repaint()


    def regenerate_bridge(self):
        self.load_bridge()



class BridgeComponentCheckbox(QWidget):
    """
    Horizontal component selector with multi-select capability
    """
    def __init__(self, parent: CAD3DWindow):
        super().__init__(parent)
        self.parent = parent

        self.setObjectName("cad_component_selector")
        self.setFixedHeight(30)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 4, 12, 4)
        layout.setSpacing(16)

        layout.addStretch()

        self.checkboxes = []

        
        self.components = [
            ("Model", None),  # Special: shows full model
            ("Girder", "Girder"),
            ("Deck", "Deck"),
            ("Cross Bracing", "Cross Bracing"),
            ("Crash Barrier", "Crash Barrier"),
            ("Median", "Median"),
            ("Railing", "Railing"),
        ]

        for label, key in self.components:
            cb = QCheckBox(label, self)
            cb.setObjectName(label)
            cb.setCursor(Qt.PointingHandCursor)

            cb.clicked.connect(
                lambda checked, k=key, c=cb: self._on_click(k, c, checked)
            )

            layout.addWidget(cb)
            self.checkboxes.append(cb)

        layout.addStretch()

        # Default selection → Model
        self.checkboxes[0].setChecked(True)

    def _on_click(self, component_key, clicked_cb, checked):
        """
        Handle multi-select logic:
        - "Model" is exclusive (unchecks all others)
        - Other components can be multi-selected
        - Selecting any component unchecks "Model"
        """
        model_cb = self.checkboxes[0]  # "Model" checkbox
        
        if component_key is None:  # "Model" clicked
            if checked:
                # Uncheck all other components
                for cb in self.checkboxes[1:]:
                    cb.blockSignals(True)
                    cb.setChecked(False)
                    cb.blockSignals(False)
                self.parent.show_full_model()
            else:
                # Don't allow unchecking Model if nothing else is selected
                if not any(cb.isChecked() for cb in self.checkboxes[1:]):
                    clicked_cb.blockSignals(True)
                    clicked_cb.setChecked(True)
                    clicked_cb.blockSignals(False)
        
        else:  # Component clicked
            if checked:
                # Uncheck "Model" when selecting a specific component
                model_cb.blockSignals(True)
                model_cb.setChecked(False)
                model_cb.blockSignals(False)
            else:
                # If all components are unchecked, check "Model"
                if not any(cb.isChecked() for cb in self.checkboxes):
                    model_cb.blockSignals(True)
                    model_cb.setChecked(True)
                    model_cb.blockSignals(False)
                    self.parent.show_full_model()
                    return
            
            # Update visibility based on selected components
            selected = [
                key for cb, (_, key) in zip(self.checkboxes[1:], self.components[1:])
                if cb.isChecked() and key is not None
            ]
            
            if selected:
                self.parent.update_component_visibility(selected)
            else:
                # If nothing selected, show full model
                model_cb.blockSignals(True)
                model_cb.setChecked(True)
                model_cb.blockSignals(False)
                self.parent.show_full_model()

# Standalone Testing----------------------------
def main():
    app = QApplication(sys.argv)
    win = CAD3DWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()