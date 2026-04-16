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

from osdagbridge.core.bridge_types.plate_girder.dto import (
    BridgeParametersDTO,
    SectionDimsDTO,
    ISectionDimsDTO,
    ShearStudParamsDTO,
    GirderSegmentDTO,
)

class CAD3DWindow(QWidget):
    """
    Main 3D CAD window for OsdagBridge.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # CAD generator
        self.generator = PlateGirderCADGenerator()

        # Internal CAD state
        self.viewer = None
        self.display = None
        self._cad_init_pending = True

        # UI + CAD setup
        self.setup_ui()
        self.init_display()  # Only initializes the viewer, does NOT render

    # ── UI SETUP ──────────────────────────────────────────────────────────────

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Component selector — hidden until render_3d_cad() is called
        self.component_selector = BridgeComponentCheckbox(self)
        self.component_selector.hide()
        self.layout.addWidget(self.component_selector)

    # ── CAD INITIALIZATION (viewer only, no render) ───────────────────────────

    def init_display(self):
        """
        Initialize the 3D viewer widget only.
        Does NOT generate or render any geometry.
        Call render_3d_cad() to render the model.
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

    def _complete_cad_init(self):
        """
        Complete CAD setup after InitDriver.
        REQUIRED for hover, selection, view cube.
        """
        self.display = self.viewer._display

        self.viewer.context = self.display.Context
        self.viewer.view = self.display.View

        self.display.set_bg_gradient_color([255, 255, 255], [126, 126, 126])
        self.viewer.context.SetAutomaticHilight(False)

        if hasattr(self.viewer, "display_view_cube"):
            self.viewer.display_view_cube()

        self.create_cad_view_controls()

    def _is_display_ready(self):
        return self.display is not None and not self._cad_init_pending

    # ── RENDER / CLEAR ────────────────────────────────────────────────────────

    def render_3d_cad(self, design_params: BridgeParametersDTO):
        """
        Generate and render the 3D bridge model on the display.
        Shows the component selector checkboxes after rendering.
        Safe to call multiple times — clears previous model first.
        """
        if not self._is_display_ready():
            return

        # Generate fresh model data
        self.generator.model_data = self.generator.generate(design_params)

        # Render on display
        self.load_bridge()

        # Show component selector
        self.component_selector.show()

    def clear_3d_cad(self):
        """
        Clear the 3D model from the display and hide the component selector.
        """
        if not self._is_display_ready():
            return

        # Clear all AIS objects from context
        if hasattr(self.viewer, "cleanup_for_new_model"):
            self.viewer.cleanup_for_new_model()
        self.display.EraseAll()
        self.display.Repaint()

        # Reset tracked objects
        self.viewer.model_ais_objects = {}
        self.viewer.model_hover_labels = {}
        if hasattr(self.viewer, "deck_texture_ais"):
            self.viewer.deck_texture_ais = []

        # Hide component selector
        self.component_selector.hide()

        # Reset checkboxes to default state (Model checked)
        self.component_selector.reset()

    # ── CAD DISPLAY ───────────────────────────────────────────────────────────
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
            cad_data.get("shear_studs", []),
            "Shear Stud",
            "Shear Stud",
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
            "Girder": ["Girder Web", "Girder Flange", "Support", "Stiffener", "Shear Stud"],
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
    
    def reset(self):
        """Reset all checkboxes to default state (Model selected, others unchecked)."""
        for cb in self.checkboxes:
            cb.blockSignals(True)
            cb.setChecked(False)
            cb.blockSignals(False)

        # Re-check "Model" as default
        self.checkboxes[0].blockSignals(True)
        self.checkboxes[0].setChecked(True)
        self.checkboxes[0].blockSignals(False)

# Standalone Testing----------------------------
def main():
    app = QApplication(sys.argv)

    bridge_parameters = BridgeParametersDTO(
        # --- Girder ---
        span_length_L=25_000,
        girder_section_d=900,
        girder_section_bf=500,
        girder_section_bf_b=500,
        girder_section_tf=260,
        girder_section_tf_b=260,
        girder_section_tw=100,
        num_girders=5,
        girder_spacing=2_750,

        # --- Geometry ---
        skew_angle=0,

        # --- Deck ---
        carriageway_width=12_000,
        deck_thickness=400,
        footpath_config="BOTH",
        footpath_width=1_500,
        railing_width=300,

        # --- Crash Barrier ---
        barrier_type="Semi-Rigid",
        crash_barrier_subtype="Double W-beam",

        # --- Median ---
        enable_median=True,
        median_type="Metallic Crash Barrier",

        # --- Railing ---
        rail_count=3,
        railing_type="rcc",

        # --- Intermediate Stiffeners ---
        include_intermediate_stiffeners=True,
        intermediate_stiffener_spacing=2_000,
        intermediate_stiffener_thickness=20,
        intermediate_stiffener_outstand=None,

        # --- End Stiffeners ---
        num_end_stiffener_pairs=4,
        end_stiffener_thickness=30,
        end_stiffener_outstand=None,

        # --- Longitudinal Stiffeners ---
        include_longitudinal_stiffeners=True,
        num_longitudinal_stiffeners=2,
        longitudinal_stiffener_thickness=20,
        longitudinal_stiffener_outstand=None,

        # --- Cross Bracing ---
        cross_bracing_spacing=4_000,
        bracing_type="X",
        x_bracket_option="BOTH",
        k_top_bracket=True,

        diagonal_section_type="ANGLE",
        diagonal_section_dims=SectionDimsDTO(leg_h=100, leg_w=50, connection_type="LONGER_LEG"),
        diagonal_thickness=5,

        top_chord_section_type="DOUBLE_CHANNEL",
        top_chord_section_dims=SectionDimsDTO(leg_h=80, leg_w=40, connection_type="LONGER_LEG"),
        top_chord_thickness=5,

        bottom_chord_section_type="ANGLE",
        bottom_chord_section_dims=SectionDimsDTO(leg_h=80, leg_w=40, connection_type="LONGER_LEG"),
        bottom_chord_thickness=5,

        # --- End Diaphragm ---
        end_diaphragm_type="Cross Bracing",
        end_diaphragm_spacing=100,
        end_diaphragm_bracing_type="K",

        end_diaphragm_diagonal_section_type="ANGLE",
        end_diaphragm_diagonal_section_dims=SectionDimsDTO(leg_h=100, leg_w=50, connection_type="LONGER_LEG"),
        end_diaphragm_diagonal_thickness=5,

        end_diaphragm_top_chord_section_type="CHANNEL",
        end_diaphragm_top_chord_section_dims=SectionDimsDTO(leg_h=80, leg_w=40, connection_type="LONGER_LEG"),
        end_diaphragm_top_chord_thickness=5,

        end_diaphragm_bottom_chord_section_type="ANGLE",
        end_diaphragm_bottom_chord_section_dims=SectionDimsDTO(leg_h=80, leg_w=40, connection_type="LONGER_LEG"),
        end_diaphragm_bottom_chord_thickness=5,

        end_diaphragm_section="I_SECTION",
        end_diaphragm_dims=ISectionDimsDTO(depth=800, flange_width=250, web_thickness=12, flange_thickness=100),

        shear_stud_params=ShearStudParamsDTO(
            base_diameter=50,
            top_diameter=70,
            base_height=150,
            top_height=50,
            num_per_section=4,
            transverse_spacing=305,
            pitch=500,
        ),
        girder_segments=[
            GirderSegmentDTO(
                length=25_000,
                D=900,
                tw=100,
                T_ft=260,
                T_fb=260,
                B_ft=500,
                B_fb=500,
            )
        ],
        girder_segments_dict=None,
    )

    win = CAD3DWindow()
    win.show()

    # Delay render until after the display is fully initialized
    QTimer.singleShot(200, lambda: win.render_3d_cad(bridge_parameters))

    sys.exit(app.exec())


if __name__ == "__main__":
    main()