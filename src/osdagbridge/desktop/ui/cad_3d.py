"""
3D CAD Viewer Window for OsdagBridge.

- Embeds CustomViewer3d
- Calls CAD generator
- Multi-select component visibility
"""

import sys
import math

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QCheckBox,
    QPushButton,
    QFrame,
    QLabel,
    QGridLayout
)
from PySide6.QtCore import QTimer, Qt

from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCC.Core.AIS import AIS_Shape
from OCC.Core.gp import gp_Pnt
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeSphere
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeEdge
from OCC.Display.backend import load_backend

try:
    from OCC.Core.AIS import AIS_TextLabel
    _HAS_AIS_TEXT = True
except ImportError:
    _HAS_AIS_TEXT = False

# Z-layer constant (resolved once at import time)
try:
    from OCC.Core.Graphic3d import Graphic3d_ZLayerId_Topmost as _Z_TOP
except ImportError:
    try:
        from OCC.Core.Graphic3d import Graphic3d_ZLayerId_Top as _Z_TOP
    except ImportError:
        _Z_TOP = None

try:
    from OCC.Core.Aspect import Aspect_TODT_NORMAL as _TODT_NORMAL
except ImportError:
    try:
        from OCC.Core.Aspect import Aspect_TODT_SUBTITLE as _TODT_NORMAL
    except ImportError:
        _TODT_NORMAL = 0  # numeric fallback

# CAD generator
from osdagbridge.core.bridge_types.plate_girder.cad_generator import (
    PlateGirderCADGenerator
)
from osdagbridge.core.bridge_types.plate_girder import results_data

# Custom 3D Viewer
from osdagbridge.desktop.ui.utils.custom_3dviewer import CustomViewer3d

from osdagbridge.core.bridge_types.plate_girder.dto import (
    BridgeParametersDTO,
    SectionDimsDTO,
    ISectionDimsDTO,
    ShearStudParamsDTO,
    GirderSegmentDTO,
)
from osdagbridge.desktop.ui.utils.custom_cursors import pointing_hand_cursor

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

        # Node state — single source of truth
        # _node_data: nid -> {x, y, z (mm), label}
        self._node_data: dict = {}
        self._members = {}

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

        self.design_params = design_params

        # Generate fresh model data
        self.generator.model_data = self.generator.generate(design_params)

        # Render on display
        self.load_bridge()

        # Show component selector
        self.component_selector.show()

        # Update info table
        if hasattr(self, "update_info_table"):
            self.update_info_table(design_params)

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
        self._node_data = {}
        self._members = {}
        self.viewer.model_ais_objects = {}
        self.viewer.model_hover_labels = {}
        if hasattr(self.viewer, "deck_texture_ais"):
            self.viewer.deck_texture_ais = []
        if hasattr(self.viewer, "set_node_hover_data"):
            self.viewer.set_node_hover_data([])
        if hasattr(self.viewer, "model_hover_labels_by_ais"):
            self.viewer.model_hover_labels_by_ais.clear()

        # Hide component selector
        self.component_selector.hide()

        # Reset checkboxes to default state (Model checked)
        self.component_selector.reset()

        # Hide the legend info table and clear its values so it never shows
        # stale data from the previous CAD model (e.g. after an unlock).
        if hasattr(self, "_info_value_labels"):
            for lbl in self._info_value_labels.values():
                lbl.setText("—")
        if hasattr(self, "_info_table") and self._info_table:
            self._info_table.hide()

        # Hide the axis triad — it belongs to a generated model only.
        triad = getattr(self.viewer, "_axis_triad", None)
        if triad is not None:
            try:
                triad.stop()
            except Exception:
                pass

        # Force a full viewport repaint so the translucent overlays don't leave
        # a faint "ghost" of their last frame on the OpenGL surface (Linux).
        try:
            self.viewer.update()
            self.display.Repaint()
        except Exception:
            pass

    # ── CAD DISPLAY ───────────────────────────────────────────────────────────
    def load_bridge(self):
        if not self._is_display_ready():
            return

        params = self.design_params
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
        def display_and_register(shapes, key, label, color, transparency=None, line_width=None, selectable=True):
            if not shapes:
                return

            if not isinstance(shapes, list):
                shapes = [shapes]

            ais_list = []

            for shp in shapes:
                kwargs = {'color': color, 'update': False}
                if transparency is not None:
                    kwargs['transparency'] = float(transparency)
                ais = display.DisplayShape(shp, **kwargs)

                ais = ais[0] if isinstance(ais, list) else ais

                if line_width is not None:
                    ais.SetWidth(line_width)
                    context.RecomputePrsOnly(ais, False)

                if selectable:
                    context.Activate(ais, 0)   # REQUIRED for hover
                else:
                    context.Deactivate(ais)
                ais_list.append(ais)

            self.viewer.model_ais_objects[key] = ais_list
            self.viewer.model_hover_labels[key] = label

      

        self.viewer.model_ais_objects = {}

        #  PLATE GIRDER (WEB + FLANGES SEPARATE COLORS) 

        display_and_register(
            cad_data.get("girder_web", []),
            "Girder Web",
            f"Girder Web\nDepth: {params.girder_section_d:.2f} mm\nWeb Thickness: {params.girder_section_tw:.2f} mm\nSteel Grade: {params.steel_grade}",
            WEB_COLOR
        )

        display_and_register(
            cad_data.get("girder_top_flanges", []),
            "Girder Top Flange",
            f"Top Flange\nWidth: {params.girder_section_bf:.2f} mm\nThickness: {params.girder_section_tf:.2f} mm\nSteel Grade: {params.steel_grade}",
            FLANGE_COLOR
        )

        display_and_register(
            cad_data.get("girder_bottom_flanges", []),
            "Girder Bottom Flange",
            f"Bottom Flange\nWidth: {params.girder_section_bf_b:.2f} mm\nThickness: {params.girder_section_tf_b:.2f} mm\nSteel Grade: {params.steel_grade}",
            FLANGE_COLOR
        )


        display_and_register(
            cad_data.get("intermediate_stiffeners", []),
            "Intermediate Stiffener",
            f"Intermediate Stiffener\nSpacing: {params.intermediate_stiffener_spacing:.2f} mm\nThickness: {params.intermediate_stiffener_thickness:.2f} mm\nSteel Grade: {params.steel_grade}",
            STIFFENER_COLOR,
            selectable=True
        )

        display_and_register(
            cad_data.get("bearing_stiffeners", []),
            "Bearing Stiffener",
            f"Bearing Stiffener\nPairs: {params.num_end_stiffener_pairs}\nThickness: {params.end_stiffener_thickness:.2f} mm\nSteel Grade: {params.steel_grade}",
            STIFFENER_COLOR,
            selectable=True
        )

        display_and_register(
            cad_data.get("longitudinal_stiffeners", []),
            "Longitudinal Stiffener",
            f"Longitudinal Stiffener\nCount: {params.num_longitudinal_stiffeners}\nThickness: {params.longitudinal_stiffener_thickness:.2f} mm\nSteel Grade: {params.steel_grade}",
            STIFFENER_COLOR,
            selectable=True
        )

        display_and_register(
            cad_data.get("shear_studs", []),
            "Shear Stud",
            f"Shear Stud\nBase Dia: {params.shear_stud_params.base_diameter:.2f} mm\nHeight: {params.shear_stud_params.base_height + params.shear_stud_params.top_height:.2f} mm\nPitch: {params.shear_stud_params.pitch:.2f} mm\nPer Section: {params.shear_stud_params.num_per_section}",
            STIFFENER_COLOR,
            selectable=False
        )

        SUPPORT_VERTICAL_COLOR   = Quantity_Color(0.0, 0.35, 0.0,  Quantity_TOC_RGB)  # Green
        SUPPORT_TRANSVERSE_COLOR = Quantity_Color(0.1,  0.1, 0.85, Quantity_TOC_RGB)  # Blue
        SUPPORT_LONGIT_COLOR     = Quantity_Color(0.85, 0.1, 0.1, Quantity_TOC_RGB)  # Red


        display_and_register(
            cad_data.get("supports_vertical",   []), 
            "Support Vertical",   
            "Support - Vertical",      
            SUPPORT_VERTICAL_COLOR,
            line_width=2.0)
        
        display_and_register(
            cad_data.get("supports_wide_horiz", []), 
            "Support Transverse", 
            "Support - Transverse",    
            SUPPORT_TRANSVERSE_COLOR,
            line_width=2.0)
        
        display_and_register(
            cad_data.get("supports_long_horiz", []), 
            "Support Longitudinal",
            "Support - Longitudinal", 
            SUPPORT_LONGIT_COLOR,
            line_width=2.0)


        display_and_register(
            cad_data.get("cross_bracings", []),
            "Cross Bracing",
            f"Cross Bracing\nType: {params.bracing_type}-Bracing\nSpacing: {params.cross_bracing_spacing:.2f} mm\nSection: {params.diagonal_section_type}\nLeg H: {params.diagonal_section_dims.leg_h:.2f} mm\nLeg W: {params.diagonal_section_dims.leg_w:.2f} mm",
            BRACING_COLOR
        )

        display_and_register(
            cad_data.get("deck_slab"),
            "Deck",
            f"Deck Slab\nThickness: {params.deck_thickness:.2f} mm\nCarriageway Width: {params.carriageway_width:.2f} mm\nConcrete Grade: {params.concrete_grade}\nFootpath: {params.footpath_config}",
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
            f"Crash Barrier\nType: {params.barrier_type}\nSubtype: {params.crash_barrier_subtype}",
            BARRIER_POST_COLOR
        )


        display_and_register(
            cad_data.get("median_barriers", []),
            "Median",
            f"Median Barrier\nType: {params.median_type}",
            BARRIER_COLOR
        )

        display_and_register(
            cad_data.get("railings", []),
            "Railing",
            f"Railing\nType: {params.railing_type.upper()}\nRails: {params.rail_count}\nWidth: {params.railing_width:.2f} mm",
            BARRIER_COLOR
        )

        # Nodes and grillage overlays
        node_positions = self._render_nodes()
        self._render_grillage(node_positions)

        # FINAL VIEW
        display.View_Iso()
        display.FitAll()

        if hasattr(self.viewer, "display_view_cube"):
            self.viewer.display_view_cube(start_triad=True)

        self.component_selector.show()

        # Trigger lookup dictionary rebuild
        self.viewer.rebuild_ais_lookup_map()
        self.component_selector.apply_selection()

    # CAD OVERLAY CONTROLS

    def create_cad_view_controls(self):
        """Create the info table overlay and wire the resize proxy."""

        # ── Info table overlay ──────────────────────────────────────────
        self._info_table = QFrame(self.viewer)
        self._info_table.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 210);
                border: 1px solid #bdbdbd;
                border-radius: 4px;
            }
        """)
        grid = QGridLayout(self._info_table)
        grid.setContentsMargins(8, 6, 8, 6)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(3)

        label_style = "font-size: 11px; color: #444; font-weight: bold; background: transparent; border: none;"
        value_style = "font-size: 11px; color: #111; background: transparent; border: none;"

        rows = [
            ("Overall Bridge Width", "—", "m"),
            ("Span Length",          "—", "m"),
            ("Girder Spacing",       "—", "m"),
            ("Deck Thickness",       "—", "mm")
        ]
        self._info_value_labels = {}
        keys = ["bridge_width", "span_length", "girder_spacing", "deck_thickness"]

        for i, (name, default, unit) in enumerate(rows):
            lbl = QLabel(name + ":")
            lbl.setStyleSheet(label_style)
            val = QLabel(default)
            val.setStyleSheet(value_style)
            unt = QLabel(unit)
            unt.setStyleSheet(value_style)
            grid.addWidget(lbl, i, 0)
            grid.addWidget(val, i, 1)
            grid.addWidget(unt, i, 2)
            self._info_value_labels[keys[i]] = val

        self._info_table.adjustSize()
        # Start hidden — the legend only appears once a CAD model is generated
        # (revealed by update_info_table). It must not show on the empty viewer.
        self._info_table.hide()
        self._position_info_table()

        self._orig_resize_event = self.viewer.resizeEvent
        self.viewer.resizeEvent = self._cad_resize_proxy

    def _cad_resize_proxy(self, event):
        if self._orig_resize_event:
            self._orig_resize_event(event)
        self._position_info_table()

    def _position_info_table(self):
        if not hasattr(self, "_info_table") or not self._info_table:
            return
        margin = 10
        h = self.viewer.height()
        tbl_h = self._info_table.height()
        tbl_w = self._info_table.width()
        self._info_table.move(margin, h - tbl_h - margin)

    def update_info_table(self, params: "BridgeParametersDTO"):
        """Populate the info table from design params."""
        if not hasattr(self, "_info_value_labels"):
            return

        # Get total bridge width from generator model data (already computed)
        model_data = getattr(self.generator, "model_data", None)
        if model_data and "total_deck_width" in model_data:
            bridge_width_mm = model_data["total_deck_width"]
        else:
            # Fallback: carriageway + footpaths
            footpath_total = 0.0
            if params.footpath_config in ("LEFT", "BOTH"):
                footpath_total += params.footpath_width
            if params.footpath_config in ("RIGHT", "BOTH"):
                footpath_total += params.footpath_width
            bridge_width_mm = params.carriageway_width + footpath_total

        self._info_value_labels["bridge_width"].setText(f"{bridge_width_mm / 1000:.2f}")
        self._info_value_labels["span_length"].setText(f"{params.span_length_L / 1000:.2f}")
        self._info_value_labels["girder_spacing"].setText(f"{params.girder_spacing / 1000:.2f}")
        self._info_value_labels["deck_thickness"].setText(f"{params.deck_thickness:.0f}")

        self._info_table.adjustSize()
        # A CAD model now exists — reveal the legend (unless the user toggled it
        # off via the toolbar; that toggle drives show/hide independently).
        self._info_table.show()
        self._position_info_table()

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

    # ── REPORT FIGURE CAPTURE ─────────────────────────────────────────────────

    def capture_for_report(self) -> dict:
        """Capture report figures from the live display. Must be called from main thread.

        Returns {attr: bytes} — PNG data in RAM only. Each OCC export writes to a
        NamedTemporaryFile, bytes are read immediately, file deleted right away.
        Nothing is written permanently to the user's disk.
        girder_top is NOT captured here; output_dock adds it via QBuffer.
        """
        import os, tempfile, logging
        _log = logging.getLogger(__name__)

        if not self._is_display_ready():
            _log.warning("capture_for_report: display not ready — skipped")
            return {}

        ALL         = ['Girder', 'Deck', 'Cross Bracing', 'Crash Barrier', 'Median', 'Railing']
        GIRDER_ONLY = ['Girder']
        GIRDER_DECK = ['Girder', 'Deck']

        def _snap(attr, components, view_fn):
            """Set visibility, render, read PNG bytes, delete temp file. Returns bytes or None."""
            tmp_path = None
            try:
                self.update_component_visibility(components)
                view_fn()
                self.display.FitAll()
                tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                tmp_path = tmp.name
                tmp.close()
                self.display.ExportToImage(tmp_path)
                if os.path.exists(tmp_path):
                    with open(tmp_path, 'rb') as fh:
                        return fh.read()
            except Exception as exc:
                _log.warning("capture_for_report: %s failed: %s", attr, exc)
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    try:
                        os.unlink(tmp_path)
                    except OSError:
                        pass
            return None

        data = {}

        # Figure 6.1 — Typical Cross Section: all components, end-on view
        b = _snap('cross_section', ALL, self.display.View_Right)
        if b: data['cross_section'] = b

        # Figure 6.2 — 3D View of Plate Girder: girders only, isometric
        b = _snap('girder_3d', GIRDER_ONLY, self.display.View_Iso)
        if b: data['girder_3d'] = b

        # Figure 6.1.3 — Top View: added by output_dock via QBuffer (skipped here)

        # Figure 6.1.1 — Overall 3D Bridge Superstructure: all components, isometric
        b = _snap('final_geometry', ALL, self.display.View_Iso)
        if b: data['final_geometry'] = b

        # Restore: show all components, iso view
        try:
            self.update_component_visibility(ALL)
            self.display.View_Iso()
            self.display.FitAll()
        except Exception:
            pass

        _log.info("capture_for_report: %d figure(s) in RAM", len(data))
        return data


    def update_component_visibility(self, selected_components: list) -> None:
        """
        Show or hide model AIS objects based on which component keys are selected.

        CALLED FROM
        ───────────
        • BridgeComponentCheckbox._apply()  (this file, below)
              When the user ticks/unticks a checkbox in the 2nd-row panel.

        • ToolBarController._cad_toggle_grillage() / _cad_toggle_node()  (toolbar_controller.py)
              When the user clicks the Grillage View or Node button on the main toolbar.
              The controller finds the hidden Grillage/Node QCheckBox in
              BridgeComponentCheckbox._checkboxes, sets its state, then calls
              BridgeComponentCheckbox._apply() which calls this method.

        PARAMETERS
        ──────────
        selected_components : list[str]
            Keys that should be VISIBLE after this call.
            Base keys  — show structural geometry:
                "Girder", "Deck", "Cross Bracing", "Crash Barrier",
                "Median", "Railing"
            Toolbar-overlay keys (checkbox-independent, never erased here):
                "Grillage"     — edge lines between nodes
                "Node"         — sphere markers at each node
        """
        if not self._is_display_ready():
            return

        context = self.viewer.context
        show_nodes = "Node" in selected_components

        # Map checkbox keys → internal model_ais_objects keys
        component_map = {
            "Girder":        ["Girder Web", "Girder Top Flange", "Girder Bottom Flange",
                              "Intermediate Stiffener", "Bearing Stiffener", "Longitudinal Stiffener",
                              "Shear Stud", "Support Vertical", "Support Transverse", "Support Longitudinal"],
            "Deck":          ["Deck"],
            "Cross Bracing": ["Cross Bracing"],
            "Crash Barrier": ["Crash Barrier", "Crash Barrier W-Beam"],
            "Median":        ["Median", "Median W-Beam"],
            "Railing":       ["Railing"],
            "Grillage":      ["Grillage"],
            "Node":          ["Node"],
        }

        # Build the set of AIS keys that should be visible
        visible_keys: set = set()
        for comp in selected_components:
            if comp in component_map:
                visible_keys.update(component_map[comp])

        # ── Toolbar-only overlays: NodeNumbers and ElementNumbers ─────────────
        # These are toggled exclusively by the toolbar buttons
        # (ToolBarController._cad_toggle_node_number / _cad_toggle_element_number)
        # and MUST NOT be touched by the checkbox-driven _apply() flow.
        # Skipping them here means they survive Grillage/Node/Deck checkbox changes.
        _TOOLBAR_OVERLAYS = {"NodeNumbers", "ElementNumbers"}

        # ── Node hover data: follow the Node checkbox (not the label toggle) ──
        if show_nodes and hasattr(self.viewer, "set_node_hover_data"):
            self.viewer.set_node_hover_data(
                [{"x": d["x"], "y": d["y"], "z": d["z"], "label": d["label"]}
                 for d in self._node_data.values()]
            )
        elif not show_nodes and hasattr(self.viewer, "set_node_hover_data"):
            self.viewer.set_node_hover_data([])

        # ── Show / hide all registered AIS objects ────────────────────────────
        for key, ais_list in self.viewer.model_ais_objects.items():
            if key in _TOOLBAR_OVERLAYS:
                continue  # toolbar-only overlays: never touched here
            should_show = key in visible_keys
            for ais in ais_list:
                try:
                    if should_show:
                        context.Display(ais, False)
                    else:
                        context.Erase(ais, False)
                except Exception:
                    pass

        # Deck textures follow the Deck checkbox
        show_deck = "Deck" in selected_components
        for ais in getattr(self.viewer, "deck_texture_ais", []):
            try:
                if show_deck:
                    context.Display(ais, False)
                else:
                    context.Erase(ais, False)
            except Exception:
                pass

        self.display.FitAll()
        self.display.Repaint()

    def regenerate_bridge(self):
        self.load_bridge()

    # ── RENDER NODES ──────────────────────────────────────────────────────────
    # Called once during load_bridge() to build node sphere AIS objects.
    # The Node toolbar button in toolbar_controller.py triggers visibility
    # changes by calling update_component_visibility() — it does NOT call
    # this method again.  Rendering happens once; visibility is toggled.

    def _render_nodes(self) -> dict:
        """
        Build node sphere markers from the live OpenSees model and register
        them in the OCC context.

        DATA SOURCE
        ───────────
        Node coordinates come from:
            results_data._build_nodes_members()
                → ops.getNodeTags()      (openseespy — live model)
                → ops.nodeCoord(n)       (metres, converted to mm here)

        WHAT IT CREATES (stored in viewer.model_ais_objects["Node"])
        ───────────────────────────────────────
        Per node, two OCC AIS_Shape objects:
          • Visible sphere (radius 65 mm, black) — what the user sees
          • Transparent pick sphere (radius 120 mm) — larger hit area for
            hover tooltips ("Node N\nX: ... m\nZ: ... m")

        RETURN VALUE
        ────────────
        dict  nid → (x_mm, y_mm, z_mm) — passed straight to _render_grillage()

        USED BY (toolbar_controller.py)
        ────────────────────────────────
        ToolBarController._cad_toggle_node() shows/hides the AIS objects
        created here by calling update_component_visibility("Node").
        """
        if not self._is_display_ready():
            return {}

        try:
            nodes, members = results_data._build_nodes_members()
        except Exception:
            return {}

        if not nodes:
            return {}

        deck_top_z = self.generator.model_data.get("deck_top_z")
        if deck_top_z is None:
            return {}

        # Unit heuristic: OpenSees uses metres; CAD uses mm.
        coords = [(float(c[0]), float(c[2])) for c in nodes.values() if c]
        max_abs = max((max(abs(x), abs(z)) for x, z in coords), default=0.0)
        scale = 1000.0 if max_abs <= 500.0 else 1.0

        skew_rad = math.radians(float(getattr(self.generator, "skew_angle", 0.0) or 0.0))
        skew_tan = math.tan(skew_rad) if abs(skew_rad) > 1e-9 else 0.0

        z_vals = [z for _, z in coords]
        z_center = 0.5 * (min(z_vals) + max(z_vals)) if z_vals and min(z_vals) >= -1e-6 else 0.0

        NODE_COLOR = Quantity_Color(0.0, 0.0, 0.0, Quantity_TOC_RGB)
        NODE_R     = 65.0    # visible sphere radius
        PICK_R     = 120.0   # larger transparent pick sphere for hover hit-testing
        z_base     = float(deck_top_z) + 2.0

        self._node_data = {}
        node_ais_list = []
        hover_nodes = []

        self.viewer.model_ais_objects.pop("Node", None)
        if hasattr(self.viewer, "set_node_hover_data"):
            self.viewer.set_node_hover_data([])
        if hasattr(self.viewer, "model_hover_labels_by_ais"):
            self.viewer.model_hover_labels_by_ais.clear()

        for nid, coord in nodes.items():
            if not coord:
                continue

            x_m, z_m = float(coord[0]), float(coord[2])
            x_mm = x_m * scale
            if skew_tan:
                # OpenSees skew is relative to Z=0, whereas CAD skew is relative to the centerline (z_center).
                # This introduces a constant horizontal offset of z_center * scale * skew_tan.
                # Subtracting this offset aligns the nodes horizontally with the CAD deck.
                x_mm -= z_center * scale * skew_tan
            y_mm = (z_m - z_center) * scale

            label = f"Node {nid}\nX: {x_m:.2f} m\nZ: {z_m:.2f} m"

            # Visible sphere
            vis = AIS_Shape(BRepPrimAPI_MakeSphere(gp_Pnt(x_mm, y_mm, z_base), NODE_R).Shape())
            vis.SetColor(NODE_COLOR)
            if _Z_TOP is not None:
                try:
                    vis.SetZLayer(_Z_TOP)
                except Exception:
                    pass
            self.viewer.context.Display(vis, False)
            node_ais_list.append(vis)

            # Transparent pick sphere (larger hit area for hover)
            pick = AIS_Shape(BRepPrimAPI_MakeSphere(gp_Pnt(x_mm, y_mm, z_base), PICK_R).Shape())
            pick.SetColor(NODE_COLOR)
            if _Z_TOP is not None:
                try:
                    pick.SetZLayer(_Z_TOP)
                except Exception:
                    pass
            try:
                pick.SetTransparency(0.97)
            except Exception:
                pass
            self.viewer.context.Display(pick, False)
            self.viewer.context.Activate(pick, 0)
            try:
                self.viewer.context.SetSelectionSensitivity(pick, 0, 30)
            except Exception:
                pass
            if hasattr(self.viewer, "model_hover_labels_by_ais"):
                self.viewer.model_hover_labels_by_ais[pick] = label
            node_ais_list.append(pick)

            hover_nodes.append({"x": x_mm, "y": y_mm, "z": z_base, "label": label})
            self._node_data[nid] = {"x": x_mm, "y": y_mm, "z": z_base, "label": label}

        self.viewer.model_ais_objects["Node"] = node_ais_list
        if hasattr(self.viewer, "set_node_hover_data"):
            self.viewer.set_node_hover_data(hover_nodes)

        # Store members for grillage
        self._members = members
        return {nid: (d["x"], d["y"], d["z"]) for nid, d in self._node_data.items()}

    # ── RENDER GRILLAGE ───────────────────────────────────────────────────────────
    # Called once during load_bridge() after _render_nodes().
    # Receives node positions from _render_nodes() and draws edge lines between
    # connected nodes using the member list from results_data._build_nodes_members().
    # The Grillage View toolbar button (toolbar_controller.py) toggles visibility
    # of these edges via update_component_visibility("Grillage").

    def _render_grillage(self, node_positions: dict) -> None:
        """Draw member edges between nodes to form the grillage overlay.

        DATA SOURCE
        ───────────
        node_positions: returned by _render_nodes() in this file.
        self._members:  member list from results_data._build_nodes_members().

        WHAT IT CREATES (stored in viewer.model_ais_objects["Grillage"])
        ───────────────────────────────────────
        AIS edge objects (thin dark lines) connecting pairs of nodes.
        Two layers are drawn when a deck slab exists — one at deck top and
        one below the slab.

        USED BY (toolbar_controller.py)
        ────────────────────────────────
        ToolBarController._cad_toggle_grillage() shows/hides the AIS objects
        created here by calling update_component_visibility("Grillage").
        """
        if not self._is_display_ready() or not node_positions:
            return

        members = getattr(self, "_members", None)
        if not members:
            return

        grillage_color = Quantity_Color(0.15, 0.15, 0.15, Quantity_TOC_RGB)
        grillage_ais = []

        deck_thickness = float(getattr(self.generator, "deck_thickness", 0.0) or 0.0)
        # Single layer at deck top; optionally a second layer below the deck slab.
        z_offsets = [0.0] + ([-deck_thickness - 4.0] if deck_thickness > 0 else [])

        for node_pair in members.values():
            if not node_pair or len(node_pair) < 2:
                continue
            p1 = node_positions.get(node_pair[0])
            p2 = node_positions.get(node_pair[1])
            if not p1 or not p2:
                continue
            for dz in z_offsets:
                edge = BRepBuilderAPI_MakeEdge(
                    gp_Pnt(p1[0], p1[1], p1[2] + dz),
                    gp_Pnt(p2[0], p2[1], p2[2] + dz),
                ).Shape()
                ais = self.display.DisplayShape(edge, color=grillage_color, update=False)
                ais = ais[0] if isinstance(ais, list) else ais
                try:
                    ais.SetWidth(2.0)
                except Exception:
                    pass
                grillage_ais.append(ais)

        if grillage_ais:
            self.viewer.model_ais_objects["Grillage"] = grillage_ais

    # ── RENDER NODE NUMBERS ───────────────────────────────────────────────────────
    # Called by update_component_visibility() when "NodeNumbers" is in the
    # selected list.  The "Node Numbers" checkbox in BridgeComponentCheckbox
    # (this file, below) triggers it through _apply() → update_component_visibility().
    # This method is NOT called from toolbar_controller.py — Node Numbers is
    # still controlled only by the 2nd-row panel checkbox.

    def _render_node_numbers(self) -> None:
        """
        Display node-ID labels in 3D world space.

        DATA SOURCE
        ───────────
        Uses self._node_data populated by _render_nodes() in this file.
        Each entry: nid → {x, y, z (mm), label}.

        WHAT IT CREATES (stored in viewer.model_ais_objects["NodeNumbers"])
        ───────────────────────────────────────
        • AIS_TextLabel per node (when pythonocc is built with text support)
          positioned 80 mm above the node sphere, drawn on the topmost Z-layer.
        • Fallback: small colour-coded sphere per node when AIS_TextLabel
          is unavailable.
        """
        if not self._is_display_ready() or not self._node_data:
            return

        # Clear any previous labels
        for ais in self.viewer.model_ais_objects.pop("NodeNumbers", []):
            try:
                self.viewer.context.Erase(ais, False)
            except Exception:
                pass

        # Very dark charcoal — visible against the light deck without a box
        text_color = Quantity_Color(0.05, 0.05, 0.05, Quantity_TOC_RGB)

        label_ais_list = []

        if _HAS_AIS_TEXT:
            for nid, d in self._node_data.items():
                try:
                    txt = AIS_TextLabel()
                    txt.SetText(str(nid))
                    txt.SetPosition(gp_Pnt(d["x"], d["y"], d["z"] + 80.0))
                    txt.SetColor(text_color)
                    try:
                        txt.SetDisplayType(_TODT_NORMAL)
                    except Exception:
                        pass
                    try:
                        txt.SetHeight(30.0)
                    except Exception:
                        pass
                    try:
                        txt.SetFlipping(True)
                    except Exception:
                        pass
                    if _Z_TOP is not None:
                        try:
                            txt.SetZLayer(_Z_TOP)
                        except Exception:
                            pass
                    self.viewer.context.Display(txt, False)
                    label_ais_list.append(txt)
                except Exception:
                    pass
        else:
            # Fallback: small coloured sphere when AIS_TextLabel unavailable
            for nid, d in self._node_data.items():
                try:
                    r = (int(nid) * 37 % 200 + 55) / 255.0
                    g = (int(nid) * 71 % 200 + 55) / 255.0
                    col = Quantity_Color(r, g, 0.9, Quantity_TOC_RGB)
                    ais = AIS_Shape(
                        BRepPrimAPI_MakeSphere(gp_Pnt(d["x"], d["y"], d["z"] + 80.0), 45.0).Shape()
                    )
                    ais.SetColor(col)
                    if _Z_TOP is not None:
                        try:
                            ais.SetZLayer(_Z_TOP)
                        except Exception:
                            pass
                    self.viewer.context.Display(ais, False)
                    label_ais_list.append(ais)
                except Exception:
                    pass

        if label_ais_list:
            self.viewer.model_ais_objects["NodeNumbers"] = label_ais_list
            try:
                self.display.Repaint()
            except Exception:
                pass

    # ── RENDER ELEMENT NUMBERS ────────────────────────────────────────────────────
    # Called by ToolBarController._cad_toggle_element_number() (toolbar_controller.py)
    # when the user clicks the Element Number button on the main toolbar.
    # ON  → renders one AIS_TextLabel per element at its mid-span point.
    # OFF → erases all AIS objects in model_ais_objects["ElementNumbers"].
    #
    # DATA SOURCE
    # ───────────
    # self._node_data : populated by _render_nodes() — nid → {x, y, z (mm)}
    # self._members   : populated by _render_nodes() — eid → [n1, n2]
    #   Both come from results_data._build_nodes_members()
    #   → ops.getNodeTags() / ops.nodeCoord() / ops.getEleTags() / ops.eleNodes()

    def _render_element_numbers(self) -> None:
        """
        Display element-ID labels at the midpoint of each member in 3D world space.

        DATA SOURCE
        ───────────
        self._node_data : nid → {x, y, z (mm)} — from _render_nodes()
        self._members   : eid → [n1, n2]        — from _render_nodes()

        WHAT IT CREATES (stored in viewer.model_ais_objects["ElementNumbers"])
        ───────────────────────────────────────────────────────────────────────
        • AIS_TextLabel per element midpoint (when pythonocc has text support)
          drawn on the topmost Z-layer in deep-orange colour to distinguish
          from the dark node-number labels.
        • Fallback: small deep-orange sphere at the midpoint when AIS_TextLabel
          is unavailable.
        """
        if not self._is_display_ready() or not self._members or not self._node_data:
            return

        # Clear any existing element-number labels
        for ais in self.viewer.model_ais_objects.pop("ElementNumbers", []):
            try:
                self.viewer.context.Erase(ais, False)
            except Exception:
                pass

        # Deep orange — distinct from node numbers (dark charcoal)
        elem_color = Quantity_Color(0.749, 0.212, 0.047, Quantity_TOC_RGB)  # #BF360C

        label_ais_list = []
        z_base = float(next(iter(self._node_data.values()), {}).get("z", 2.0))

        if _HAS_AIS_TEXT:
            for eid, (n1, n2) in self._members.items():
                d1 = self._node_data.get(n1)
                d2 = self._node_data.get(n2)
                if d1 is None or d2 is None:
                    continue
                mx = (d1["x"] + d2["x"]) / 2.0
                my = (d1["y"] + d2["y"]) / 2.0
                try:
                    txt = AIS_TextLabel()
                    txt.SetText(f"E{eid}")
                    txt.SetPosition(gp_Pnt(mx, my, z_base + 40.0))
                    txt.SetColor(elem_color)
                    try:
                        txt.SetDisplayType(_TODT_NORMAL)
                    except Exception:
                        pass
                    try:
                        txt.SetHeight(22.0)
                    except Exception:
                        pass
                    try:
                        txt.SetFlipping(True)
                    except Exception:
                        pass
                    if _Z_TOP is not None:
                        try:
                            txt.SetZLayer(_Z_TOP)
                        except Exception:
                            pass
                    self.viewer.context.Display(txt, False)
                    label_ais_list.append(txt)
                except Exception:
                    pass
        else:
            # Fallback: small orange sphere at element midpoint
            for eid, (n1, n2) in self._members.items():
                d1 = self._node_data.get(n1)
                d2 = self._node_data.get(n2)
                if d1 is None or d2 is None:
                    continue
                mx = (d1["x"] + d2["x"]) / 2.0
                my = (d1["y"] + d2["y"]) / 2.0
                try:
                    ais = AIS_Shape(
                        BRepPrimAPI_MakeSphere(
                            gp_Pnt(mx, my, z_base + 40.0), 30.0
                        ).Shape()
                    )
                    ais.SetColor(elem_color)
                    if _Z_TOP is not None:
                        try:
                            ais.SetZLayer(_Z_TOP)
                        except Exception:
                            pass
                    self.viewer.context.Display(ais, False)
                    label_ais_list.append(ais)
                except Exception:
                    pass

        if label_ais_list:
            self.viewer.model_ais_objects["ElementNumbers"] = label_ais_list
        try:
            self.display.Repaint()
        except Exception:
            pass

class BridgeComponentCheckbox(QWidget):
    """
    The 2nd-row horizontal panel shown below the 3D CAD view.
    Provides checkboxes for toggling structural components and overlays.

    ROLE IN THE APPLICATION
    ─────────────────────
    This widget owns and drives CAD3DWindow.update_component_visibility().
    The main ToolBar (toolbar_controller.py) is a SECONDARY controller that
    also drives visibility — it does so by finding the hidden Grillage/Node
    checkboxes in self._checkboxes and calling self._apply() directly.

    WHAT EACH CHECKBOX DOES
    ───────────────────────
    • Bridge (key=None)  — pseudo-checkbox: when checked, shows all base
      structural components (Girder, Deck, Cross Bracing, Crash Barrier,
      Median, Railing) at once.  Overlay keys are independent.
    • Individual base checkboxes (Girder, Deck, …) — show/hide each
      structural component individually.
    • Grillage view (hidden) — show/hide grillage edge lines.
      Created by _render_grillage() (this file).  Controlled exclusively
      from the main toolbar via ToolBarController (toolbar_controller.py).
    • Node (hidden) — show/hide node sphere markers.
      Created by _render_nodes() (this file).  Controlled exclusively
      from the main toolbar via ToolBarController (toolbar_controller.py).
    • Node Numbers — show/hide node-ID text labels.
      Created by _render_node_numbers() (this file).
    """

    # (label, internal key)
    # key=None  → "Model" pseudo-checkbox (selects all base components)
    # key in OVERLAY_KEYS → independent toggle, not affected by Model
    COMPONENTS = [
        ("Bridge",         None),
        ("Girder",        "Girder"),
        ("Deck",          "Deck"),
        ("Cross Bracing", "Cross Bracing"),
        ("Crash Barrier", "Crash Barrier"),
        ("Median",        "Median"),
        ("Railing",       "Railing"),
        ("Grillage view", "Grillage"),
        ("Node",          "Node"),
        ("Node Numbers",  "NodeNumbers"),
    ]
    OVERLAY_KEYS = {"Grillage", "Node", "NodeNumbers"}

    def __init__(self, parent: CAD3DWindow):
        super().__init__(parent)
        self._cad = parent

        self.setObjectName("cad_component_selector")
        self.setFixedHeight(30)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 4, 12, 4)
        layout.setSpacing(16)
        layout.addStretch()

        self._checkboxes: list[QCheckBox] = []
        for label, key in self.COMPONENTS:
            cb = QCheckBox(label, self)
            cb.setObjectName(label)
            cb.setCursor(pointing_hand_cursor())
            cb.clicked.connect(lambda checked, k=key, c=cb: self._on_click(k, c, checked))
            layout.addWidget(cb)
            self._checkboxes.append(cb)

        # Hide "Grillage view", "Node", and "Node Numbers" from the panel —
        # these are now controlled exclusively from the main ToolBar (toolbar_controller.py).
        # The checkboxes still exist in _checkboxes so the toolbar handler
        # can find and update them; they are just not visible to the user.
        for cb in self._checkboxes:
            if cb.text() in ("Grillage view", "Node", "Node Numbers"):
                cb.hide()

        layout.addStretch()

        # Default: Model checked; overlays off
        self._checkboxes[0].setChecked(True)

    # ── Maintain a back-compat alias ──────────────────────────────────────────
    @property
    def checkboxes(self):
        return self._checkboxes

    @property
    def components(self):
        return self.COMPONENTS

    # ── Click logic ───────────────────────────────────────────────────────────

    def _on_click(self, key, cb, checked):
        model_cb = self._checkboxes[0]

        if key is None:                        # "Model" clicked
            if checked:
                # Uncheck individual base components, keep overlays as-is
                for c, (_, k) in zip(self._checkboxes[1:], self.COMPONENTS[1:]):
                    if k and k not in self.OVERLAY_KEYS:
                        c.blockSignals(True)
                        c.setChecked(False)
                        c.blockSignals(False)
            else:
                if not self._any_base_checked():
                    cb.blockSignals(True)
                    cb.setChecked(True)
                    cb.blockSignals(False)
            self._apply()
            return

        if key in self.OVERLAY_KEYS:
            self._apply()
            return

        # Base component clicked
        if checked:
            model_cb.blockSignals(True)
            model_cb.setChecked(False)
            model_cb.blockSignals(False)
        else:
            if not self._any_base_checked():
                model_cb.blockSignals(True)
                model_cb.setChecked(True)
                model_cb.blockSignals(False)
        self._apply()

    def _any_base_checked(self) -> bool:
        return any(
            cb.isChecked()
            for cb, (_, k) in zip(self._checkboxes[1:], self.COMPONENTS[1:])
            if k and k not in self.OVERLAY_KEYS
        )

    def _collect(self) -> list:
        model_checked = self._checkboxes[0].isChecked()
        result = []
        for cb, (_, key) in zip(self._checkboxes[1:], self.COMPONENTS[1:]):
            if not key:
                continue
            if key in self.OVERLAY_KEYS:
                if cb.isChecked():
                    result.append(key)
            elif model_checked or cb.isChecked():
                result.append(key)
        return result

    def _apply(self):
        selected = self._collect()
        if selected:
            self._cad.update_component_visibility(selected)
            return
        # Nothing selected → fall back to Model
        self._checkboxes[0].blockSignals(True)
        self._checkboxes[0].setChecked(True)
        self._checkboxes[0].blockSignals(False)
        selected = self._collect()
        if selected:
            self._cad.update_component_visibility(selected)
        else:
            self._cad.show_full_model()

    def apply_selection(self):
        """Public entry-point called after load_bridge to apply default state."""
        self._apply()

    # ── NAVIGATION TOGGLES ────────────────────────────────────────────────────
    # These methods set the OCC viewer's navigation mode.
    # They are called from ToolBarController (toolbar_controller.py):
    #   • _cad_toggle_rotate()       → calls _on_rotate_toggled(want)
    #   • _cad_toggle_pan()          → calls _on_pan_toggled(want)
    #   • _cad_toggle_zoom_window()  → calls _on_zoom_window_toggled(want)
    # Each method passes the nav mode to CustomViewer3d.set_navigation_mode()
    # which is defined in custom_3dviewer.py.

    def _on_rotate_toggled(self, checked: bool) -> None:
        """Called by ToolBarController._cad_toggle_rotate() (toolbar_controller.py).
        Sets NavMode.ROTATE on the OCC viewer (custom_3dviewer.py) when checked,
        or clears the nav mode when unchecked."""
        from osdagbridge.desktop.ui.utils.custom_3dviewer import NavMode
        viewer = self._cad.viewer
        if viewer is None:
            return
        if checked:
            viewer.set_navigation_mode(NavMode.ROTATE)
        else:
            viewer.set_navigation_mode(None)

    def _on_pan_toggled(self, checked: bool) -> None:
        """Called by ToolBarController._cad_toggle_pan() (toolbar_controller.py).
        Sets NavMode.PAN on the OCC viewer (custom_3dviewer.py) when checked,
        or clears the nav mode when unchecked."""
        from osdagbridge.desktop.ui.utils.custom_3dviewer import NavMode
        viewer = self._cad.viewer
        if viewer is None:
            return
        if checked:
            viewer.set_navigation_mode(NavMode.PAN)
        else:
            viewer.set_navigation_mode(None)

    def _on_zoom_window_toggled(self, checked: bool) -> None:
        """Called by ToolBarController._cad_toggle_zoom_window() (toolbar_controller.py).
        Sets NavMode.ZOOM_WINDOW on the OCC viewer (custom_3dviewer.py) when checked,
        or clears the nav mode when unchecked."""
        from osdagbridge.desktop.ui.utils.custom_3dviewer import NavMode
        viewer = self._cad.viewer
        if viewer is None:
            return
        if checked:
            viewer.set_navigation_mode(NavMode.ZOOM_WINDOW)
        else:
            viewer.set_navigation_mode(None)

    def reset(self):
        """Reset to default: Model checked, all others unchecked, nav mode off."""
        for cb in self._checkboxes:
            cb.blockSignals(True)
            cb.setChecked(False)
            cb.blockSignals(False)
        self._checkboxes[0].blockSignals(True)
        self._checkboxes[0].setChecked(True)
        self._checkboxes[0].blockSignals(False)

        if self._cad.viewer is not None:
            self._cad.viewer.set_navigation_mode(None)


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