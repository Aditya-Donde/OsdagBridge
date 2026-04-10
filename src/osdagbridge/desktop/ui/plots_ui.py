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
    QHeaderView, QPushButton, QDialog
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings
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

        # Populated by setup() after bridge analysis completes
        self._ds_all = None
        self._nodes = {}
        self._members = {}

        layout = QVBoxLayout(self)
        top = QHBoxLayout()

        # ---------- LOADCASE ----------
        top.addWidget(QLabel("Load case:"))
        self.combo = QComboBox()
        self.combo.currentTextChanged.connect(self.update_plot)
        top.addWidget(self.combo)

        # ---------- FORCE ----------
        top.addWidget(QLabel("Force:"))
        self.force_combo = QComboBox()
        self.force_combo.addItems(list(FORCE_MAP.keys()))
        self.force_combo.setCurrentText("Vy")
        self.force_combo.currentTextChanged.connect(self.update_plot)
        top.addWidget(self.force_combo)

        # ---------- CONTOUR CHECKBOX ----------
        self.contour = QCheckBox("Contour (Moments only)")
        self.contour.stateChanged.connect(self.update_plot)
        top.addWidget(self.contour)
        
        top.addStretch()
        layout.addLayout(top)

        # ---------- MAIN BROWSER AREA ----------
        self.web = QWebEngineView()
        
        # Stops Qt from painting a blank background behind the web viewer
        self.web.setAttribute(Qt.WA_OpaquePaintEvent)
        self.web.setAttribute(Qt.WA_NoSystemBackground)
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

    def setup(self, ds_all, loadcases, nodes, members):
        """Populate the widget with bridge analysis results. Call after design() completes."""
        self._ds_all = ds_all
        self._nodes = nodes
        self._members = members

        self.combo.blockSignals(True)
        self.combo.clear()
        self.combo.addItems(loadcases)
        self.combo.blockSignals(False)

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
        if self._ds_all is None:
            return

        loadcase = self.combo.currentText()
        force_key = self.force_combo.currentText()
        ds = self._ds_all.sel(Loadcase=loadcase)

        is_force = force_key.startswith("F") 
        is_moment = force_key.startswith("M") 

        if is_force:
            self.contour.blockSignals(True)
            self.contour.setChecked(False)
            self.contour.setEnabled(False)
            self.contour.blockSignals(False)
            
            self.stats_dict = {}
            plot_json = build_figure_sfd(ds, force_key, self._nodes, self._members)

        elif is_moment:
            self.contour.setEnabled(True)

            if self.contour.isChecked():
                plot_json = build_figure_bmd_contour(ds, force_key, self._nodes, self._members)
                self.stats_dict = {}
            else:
                plot_json, self.stats_dict = build_figure_bmd(ds, force_key, self._nodes, self._members)
                
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