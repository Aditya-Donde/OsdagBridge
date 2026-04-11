import sys
import os
import json

# Performance Flags: Tuned for Screen Recording / Meetings on Windows
os.environ["QT_OPENGL"] = "software"
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
    "--ignore-gpu-blocklist "
    "--enable-gpu-rasterization "
    "--enable-webgl "
    "--enable-transparent-visuals "
    "--disable-software-rasterizer "
    "--disable-gpu-driver-bug-workarounds"
    "--use-angle=d3d11 "
)

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QCheckBox, QTableWidget, QTableWidgetItem, 
    QHeaderView, QPushButton, QDialog, QDoubleSpinBox
)
from PySide6.QtGui import QPalette
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings, QWebEnginePage
from PySide6.QtCore import QUrl, Qt, QPoint, QObject, Slot, Signal
from PySide6.QtWebChannel import QWebChannel

# --- IMPORT THE BACKEND LOGIC ---
from osdagbridge.core.bridge_types.plate_girder.plots_widget import (
    build_figure_sfd,
    build_figure_bmd,
    build_figure_bmd_contour,
    FORCE_MAP,
)

# =========================================================
# THE RAM-ONLY FRONTEND
# =========================================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
    <style>
        body { margin: 0; padding: 0; background-color: white; overflow: hidden; }
        #plot_div { width: 100vw; height: 100vh; }
    </style>
</head>
<body>
    <div id="plot_div"></div>

    <script>
        var pyBackend = null;

        // Initialize QWebChannel
        new QWebChannel(qt.webChannelTransport, function(channel) {
            pyBackend = channel.objects.backend;

            // Listen for data from Python
            pyBackend.newPlotData.connect(function(jsonString) {
                renderPlot(jsonString);
            });

            // Tell Python the page is ready
            pyBackend.pageReady();
        });

        function renderPlot(jsonString) {
            var figure = JSON.parse(jsonString);
            var config = { displayModeBar: true, responsive: true };

            Plotly.react('plot_div', figure.data, figure.layout, config).then(function() {
                var targetDiv = document.getElementById('plot_div');
                Plotly.Plots.resize(targetDiv);

                if (!targetDiv.hasRelayoutListener) {
                    targetDiv.on('plotly_relayout', function(eventdata) {
                        var eventString = JSON.stringify(eventdata);
                        if (eventString && eventString.includes('SHOW_SUMMARY')) {
                            // Call Python natively! No console hacks.
                            pyBackend.requestSummaryDialog();
                            setTimeout(function() {
                                Plotly.relayout('plot_div', {meta: "CLEAR"});
                            }, 100);
                        }
                    });
                    targetDiv.hasRelayoutListener = true;
                }
            });
        }
    </script>
</body>
</html>
"""

class DebugWebPage(QWebEnginePage):
    """Intercepts hidden browser errors and prints them to the Python terminal."""
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        print(f"[BROWSER ERROR] Line {lineNumber}: {message}")

class BridgeBackend(QObject):
    """The QWebChannel translator between Python and JavaScript."""
    
    # Signal: Python uses this to push JSON data to JavaScript
    newPlotData = Signal(str)

    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app

    @Slot()
    def pageReady(self):
        """JavaScript calls this when the page is fully loaded."""
        self.main_app.update_plot()

    @Slot()
    def requestSummaryDialog(self):
        """JavaScript calls this when the 'SUMMARY' button is clicked."""
        self.main_app.show_summary_dialog()


class SummaryDialog(QDialog):
    """A floating tool palette that hovers over the main UI without disturbing it."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Extreme Values")
        
        self.setWindowFlags(Qt.Tool | Qt.WindowStaysOnTopHint)
        self.resize(350, 250)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Girder", "Max (N mm)", "Min (N mm)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

    def update_data(self, stats):
        self.table.setRowCount(len(stats))
        for row, (girder, vals) in enumerate(stats.items()):
            item_girder = QTableWidgetItem(girder)
            item_max = QTableWidgetItem(f"{vals['max']:.2f}")
            item_min = QTableWidgetItem(f"{vals['min']:.2f}")
            
            item_max.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            item_min.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            self.table.setItem(row, 0, item_girder)
            self.table.setItem(row, 1, item_max)
            self.table.setItem(row, 2, item_min)


class PlotWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Plate Girder Results")

        # --- THE FIX: We now store the Handler and the current state ---
        self.results_handler = None
        self._current_loadcase = None
        self._current_force = None
        # --------------------------------------------------------------

        layout = QVBoxLayout(self)
        top = QHBoxLayout()

        # 1. ADD STRETCH FIRST! 
        # This acts like a giant invisible spring that pushes everything after it to the right.
        top.addStretch()

        # ---------- CONTOUR CHECKBOX ----------
        self.contour = QCheckBox("Contour (Moments only)")
        self.contour.setStyleSheet("color: black; font-weight: bold;")
        self.contour.setEnabled(False) # Disabled by default until a moment is loaded
        self.contour.toggled.connect(lambda _: self.update_plot()) # lambda ignores the checked boolean argument
        top.addWidget(self.contour)

        # ---------- SCALE FACTOR ----------
        lbl_scale = QLabel("Scale:")
        lbl_scale.setStyleSheet("color: black; font-weight: bold; font-size: 12px;")
        top.addWidget(lbl_scale)

        self.scale_spinbox = QDoubleSpinBox()
        self.scale_spinbox.setMinimumWidth(80)
        self.scale_spinbox.setMinimumHeight(30)
        
        palette = self.scale_spinbox.palette()
        palette.setColor(QPalette.Text, Qt.black)
        palette.setColor(QPalette.ButtonText, Qt.black)
        self.scale_spinbox.setPalette(palette)
        
        self.scale_spinbox.setRange(0.1, 50.0)    
        self.scale_spinbox.setValue(1.0)          
        self.scale_spinbox.setSingleStep(0.5)     
        
        self.scale_spinbox.valueChanged.connect(lambda _: self.update_plot())
        top.addWidget(self.scale_spinbox)
        # ---------------------------------------

        layout.addLayout(top)

        # ---------- MAIN BROWSER AREA ----------
        self.web = QWebEngineView()
        # debug page
        self.debug_page = DebugWebPage(self.web)
        self.web.setPage(self.debug_page)
        
        self.web.page().setBackgroundColor(Qt.white)

        settings = self.web.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        layout.addWidget(self.web)

        # ---------- INITIALIZATION & QWEBCHANNEL ----------
        self.stats_dict = {}  
        self.summary_dialog = SummaryDialog(self)

        self.channel = QWebChannel()
        self.backend = BridgeBackend(self)
        
        self.channel.registerObject("backend", self.backend)
        self.web.page().setWebChannel(self.channel)

        # Inject HTML directly into memory
        self.web.setHtml(HTML_TEMPLATE, QUrl("qrc:/"))

    def setup(self, results_handler, loadcases):
        """Populate the widget using the backend Analysis Results handler."""
        self.results_handler = results_handler
        # We NO LONGER call self.update_plot() here!
        # We wait for the Output Dock to pass us the selected values.

    def show_summary_dialog(self):
        """Pops up the dialog perfectly in the top-left corner of the web view."""
        if not self.stats_dict:
            return

        self.summary_dialog.update_data(self.stats_dict)
        self.summary_dialog.show()
        self.summary_dialog.raise_()
        self.summary_dialog.activateWindow()

        # Calculate exactly where the top-left of the 3D plot is on the screen
        top_left_corner = self.web.mapToGlobal(QPoint(15, 15))
        self.summary_dialog.move(top_left_corner)

    def update_plot(self, loadcase: str = None, force_key: str = None):
        """Generates the plot. Caches the loadcase and force_key for UI interactions."""
        if self.results_handler is None:
            return

        # Cache the values! If the OutputDock sends new ones, save them.
        # If the user just clicks "Scale" or "Contour", reuse the saved ones.
        if loadcase is not None:
            self._current_loadcase = loadcase
        if force_key is not None:
            self._current_force = force_key

        # Safety check: if we haven't received a loadcase/force yet, do nothing.
        if not self._current_loadcase or not self._current_force:
            return

        # Use the cached values for the rest of the function
        active_lc = self._current_loadcase
        active_force = self._current_force
        scale_val = self.scale_spinbox.value()

        is_force = active_force.startswith("F") or active_force.startswith("V")
        is_moment = active_force.startswith("M") 

        if is_force:
            self.contour.blockSignals(True)
            self.contour.setChecked(False)
            self.contour.setEnabled(False)
            self.contour.blockSignals(False)
            
            self.stats_dict = {}
            plot_json = build_figure_sfd(self.results_handler, active_lc, active_force, scale_val)

        elif is_moment:
            self.contour.setEnabled(True)

            if self.contour.isChecked():
                plot_json = build_figure_bmd_contour(self.results_handler, active_lc, active_force, scale_val)
                self.stats_dict = {}
            else:
                plot_json, self.stats_dict = build_figure_bmd(self.results_handler, active_lc, active_force, scale_val)

                if self.summary_dialog.isVisible():
                    self.summary_dialog.update_data(self.stats_dict)
        else:
            raise ValueError(f"Unsupported force: {active_force}")

        # -------- INJECT PLOT VIA QWEBCHANNEL --------
        self.backend.newPlotData.emit(plot_json)


# ======================= MAIN
if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = PlotWidget()
    w.resize(1200, 800)
    w.show()
    sys.exit(app.exec())