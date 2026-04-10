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

        # --- THE FIX: We now store the Handler, not raw data arrays ---
        self.results_handler = None
        # --------------------------------------------------------------

        layout = QVBoxLayout(self)
        top = QHBoxLayout()

        # ---------- LOADCASE ----------
        lbl_load = QLabel("Load case:")
        lbl_load.setStyleSheet("color: black; font-weight: bold; font-size: 12px;") # Force visibility!
        top.addWidget(lbl_load)
        
        self.combo = QComboBox()
        self.combo.setMinimumWidth(150) # Stop it from vanishing when empty
        self.combo.setStyleSheet("color: black; background-color: white; border: 1px solid gray;")
        self.combo.currentTextChanged.connect(self.update_plot)
        top.addWidget(self.combo)

        # ---------- FORCE ----------
        lbl_force = QLabel("Force:")
        lbl_force.setStyleSheet("color: black; font-weight: bold; font-size: 12px;") 
        top.addWidget(lbl_force)
        
        self.force_combo = QComboBox()
        self.force_combo.setMinimumWidth(80) 
        self.force_combo.setStyleSheet("color: black; background-color: white; border: 1px solid gray;")
        self.force_combo.addItems(list(FORCE_MAP.keys()))
        self.force_combo.setCurrentText("Vy")
        self.force_combo.currentTextChanged.connect(self.update_plot)
        top.addWidget(self.force_combo)

        # ---------- CONTOUR CHECKBOX ----------
        self.contour = QCheckBox("Contour (Moments only)")
        self.contour.setStyleSheet("color: black; font-weight: bold;")
        self.contour.stateChanged.connect(self.update_plot)
        top.addWidget(self.contour)

       # ---------- NEW: SCALE FACTOR ----------
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

        top.addStretch()
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

    # --- THE FIX: We now accept the results_handler instead of raw data ---
    def setup(self, results_handler, loadcases):
        """Populate the widget using the backend Analysis Results handler."""
        self.results_handler = results_handler

        self.combo.blockSignals(True)
        self.combo.clear()
        self.combo.addItems(loadcases)
        self.combo.blockSignals(False)

        self.update_plot()
    # ----------------------------------------------------------------------

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

    def update_plot(self):
        # --- THE FIX: Check for handler existence ---
        if self.results_handler is None:
            return

        loadcase = self.combo.currentText()
        force_key = self.force_combo.currentText()
        scale_val = self.scale_spinbox.value()

        is_force = force_key.startswith("F") 
        is_moment = force_key.startswith("M") 

        if is_force:
            self.contour.blockSignals(True)
            self.contour.setChecked(False)
            self.contour.setEnabled(False)
            self.contour.blockSignals(False)
            
            self.stats_dict = {}
            # --- THE FIX: Pass the handler and the loadcase name ---
            plot_json = build_figure_sfd(self.results_handler, loadcase, force_key, scale_val)

        elif is_moment:
            self.contour.setEnabled(True)

            if self.contour.isChecked():
                # --- THE FIX: Pass the handler and the loadcase name ---
                plot_json = build_figure_bmd_contour(self.results_handler, loadcase, force_key, scale_val)
                self.stats_dict = {}
            else:
                # --- THE FIX: Pass the handler and the loadcase name ---
                plot_json, self.stats_dict = build_figure_bmd(self.results_handler, loadcase, force_key, scale_val)

                if self.summary_dialog.isVisible():
                    self.summary_dialog.update_data(self.stats_dict)

        else:
            raise ValueError(f"Unsupported force: {force_key}")

        # -------- INJECT PLOT VIA QWEBCHANNEL --------
        # Emits the raw JSON string perfectly without double-encoding it
        self.backend.newPlotData.emit(plot_json)


# ======================= MAIN
if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = PlotWidget()
    w.resize(1200, 800)
    w.show()
    sys.exit(app.exec())