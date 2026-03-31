import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QFile, QTextStream
from osdagbridge.desktop.resources import resources_rc

# Import template_page
from osdagbridge.desktop.ui.template_page import CustomWindow
from osdagbridge.core.bridge_types.plate_girder.ui_fields import FrontendData

def load_stylesheet():
    """Load the global QSS stylesheet from resources."""
    file = QFile(":/themes/lightstyle.qss")
    if file.open(QFile.ReadOnly | QFile.Text):
        stream = QTextStream(file)
        stylesheet = stream.readAll()
        file.close()
        return stylesheet
    return ""

def main():
    # Create the Qt application instance
    app = QApplication(sys.argv)
    
    # Load and apply the global stylesheet
    stylesheet = load_stylesheet()
    if stylesheet:
        app.setStyleSheet(stylesheet)
    
    window = CustomWindow("Osdag Bridge", FrontendData)
    window.showMaximized()
    window.show()

    # --- UI Testing Pipeline ---
    from osdagbridge.desktop.ui.dialogs.steel_design import SteelDesign
    from osdagbridge.core.bridge_types.plate_girder.analyser import (
        BridgeGrillageModel, GrillageGeometry, SectionProperties, MaterialProperties,
        m, kN, MPa, GPa
    )
    from PySide6.QtCore import QTimer

    print("Running temporary analyser pipeline for UI testing...")
    bridge = BridgeGrillageModel()
    bridge.set_geometry(GrillageGeometry(
        L=33.5 * m,
        n_l=7,
        n_t=11,
        edge_dist=0 * m,
        ext_to_int_dist=2.2775 * m,
        angle=0,
        carriageway_width=10.0 * m,
        crash_barrier_width=0.45 * m,
        footpath_width=1.50 * m,
        railing_width=0.30 * m,
        median_width=0.0 * m,
        no_of_footpaths=2,
    ))

    bridge.create_sections(
        longitudinal=SectionProperties(1.025, 0.1878, 0.3694, 0.3634, 0.4979, 0.309),
        edge_longitudinal=SectionProperties(0.934, 0.1857, 0.3478, 0.213602, 0.444795, 0.258704),
        transverse=SectionProperties(0.504, 5.22303e-3, 1.3608e-3, 0.32928, 0.42, 0.42),
        end_transverse=SectionProperties(0.252, 2.5012e-3, 0.6804e-3, 0.04116, 0.21, 0.21),
    )

    bridge.create_material(MaterialProperties(
        material="steel", E=200 * GPa, v=0.3, rho=78.5 * kN / m ** 3, Fy=250 * MPa, E0=200 * GPa, b=0.01
    ))

    bridge.create_model()
    bridge.create_self_weight_load()
    bridge.create_deck_load()
    results = bridge.analyze()
    model = bridge.model
    print("Analysis complete. Results:", type(results))

    global _steel_design_dlg
    _steel_design_dlg = SteelDesign(parent=window)
    _steel_design_dlg._data_initialized = False
    
    def _inject_and_plot():
        dlg = _steel_design_dlg
        try:
            dlg.graph_engine._cached_model   = model
            dlg.graph_engine._cached_results = results

            dlg.graph_engine.build_girder_map()
            print("Girder map built:", dlg.graph_engine._girder_map)

            dlg._populate_member_combo()
            dlg._populate_load_combo()
            dlg._data_initialized = True

            dlg.tabs.setCurrentIndex(1)
            dlg._update_analysis_plots()
        except Exception as e:
            import traceback
            print("ERROR in UI testing injection:")
            traceback.print_exc()

    _steel_design_dlg.show()
    QTimer.singleShot(200, _inject_and_plot)
    # ---------------------------

    # Execute the event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
