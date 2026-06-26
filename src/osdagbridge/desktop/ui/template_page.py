import os, yaml
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QMenuBar, QSplitter, QSizePolicy, QPushButton, QLineEdit, QComboBox, QFileDialog,
)
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtCore import Qt, QFile, QTextStream, Signal, QTimer, QObject, QEvent, QThread
from PySide6.QtGui import QIcon, QAction, QKeySequence

from osdagbridge.desktop.ui.docks.input_dock import InputDock
from osdagbridge.desktop.ui.docks.output_dock import OutputDock
from osdagbridge.desktop.ui.docks.log_dock import LogDock
from osdagbridge.desktop.ui.docks.cad_dual_view import BridgeDualCADWidget
from osdagbridge.desktop.ui.dialogs.additional_input.additional_inputs import AdditionalInputs
from osdagbridge.desktop.ui.dialogs.custom_messagebox import CustomMessageBox, MessageBoxType
from osdagbridge.desktop.ui.dialogs.loading_popup import LoadingDialogManager
from osdagbridge.desktop.ui.cad_3d import CAD3DWindow

from osdagbridge.core.bridge_types.plate_girder.ui_fields import FrontendData
from osdagbridge.core.bridge_types.plate_girder.defaults import BASIC_INPUT_DICT, solve_extend_basic_input_dict
from osdagbridge.core.utils.common import *
from osdagbridge.core.utils.osi_validator import validate_osi_inputs
from osdagbridge.core.utils.logger import bridge_logger
from osdagbridge.desktop.ui.utils.custom_widgets import ToolBarWidget
from osdagbridge.desktop.ui.utils.custom_cursors import pointing_hand_cursor

class LoggerStdoutRedirector:
    def __init__(self, logger_func, original_stdout=None):
        self.logger_func = logger_func
        self.original_stdout = original_stdout
        self._buffer = []

    def write(self, string):
        if self.original_stdout:
            try:
                self.original_stdout.write(string)
                self.original_stdout.flush()
            except Exception:
                pass
        if not string:
            return
        self._buffer.append(string)
        if "\n" in string:
            full_text = "".join(self._buffer)
            self._buffer = []
            lines = full_text.split("\n")
            for line in lines[:-1]:
                if line.strip():
                    self.logger_func(line)
            if lines[-1]:
                self._buffer.append(lines[-1])

    def flush(self):
        if self.original_stdout:
            try:
                self.original_stdout.flush()
            except Exception:
                pass
        if self._buffer:
            full_text = "".join(self._buffer)
            self._buffer = []
            if full_text.strip():
                self.logger_func(full_text)

    def reconfigure(self, *args, **kwargs):
        if self.original_stdout and hasattr(self.original_stdout, 'reconfigure'):
            try:
                self.original_stdout.reconfigure(*args, **kwargs)
            except Exception:
                pass

    def isatty(self):
        if self.original_stdout and hasattr(self.original_stdout, 'isatty'):
            try:
                return self.original_stdout.isatty()
            except Exception:
                pass
        return False


class InputBlockerFilter(QObject):
    def __init__(self, target_widget):
        super().__init__()
        self.target = target_widget

    def eventFilter(self, obj, event):
        if self.target and isinstance(obj, QWidget) and (obj == self.target or self.target.isAncestorOf(obj)):
            if event.type() in (
                QEvent.Type.MouseButtonPress,
                QEvent.Type.MouseButtonRelease,
                QEvent.Type.MouseButtonDblClick,
                QEvent.Type.KeyPress,
                QEvent.Type.KeyRelease,
                QEvent.Type.Wheel,
                QEvent.Type.ContextMenu,
                QEvent.Type.Close
            ):
                event.accept()
                return True
        return False


class CustomWindow(QWidget):
    export_finished = Signal(bool, str)
    # Thread-safe relay for bridge_logger messages: the design run now executes on
    # a worker thread, so UI observers (loading popup) must not be called directly
    # from logger callbacks. The relay's .emit is registered with bridge_logger and
    # Qt queues cross-thread emissions onto the GUI thread.
    logger_message = Signal(str, str)

    def __init__(self, title: str, backend: object, parent=None):
        super().__init__()
        self.parent = parent
        self.backend = backend()
        
        # Connect export signal to main-thread handler
        self.export_finished.connect(self.on_export_finished)

        # Source for all input values.
        # Initialised from BASIC_INPUT_DICT; updated live as the user edits fields.
        self.input_dict = dict(BASIC_INPUT_DICT)

        # AdditionalInputs dialog 
        self._additional_inputs_dialog: AdditionalInputs | None = None
      
        # AdditionalInputs - Created once on first use, shown/hidden thereafter.
        self._get_additional_inputs()

        self.setWindowTitle(title)
        self.setStyleSheet(
            """
            QWidget {
                background-color: #ffffff;
                margin: 0px;
                padding: 0px;
            }

            /* ===== SLIM SCROLLBARS (GLOBAL) ===== */

            QScrollBar:vertical {
                width: 8px;
                background: transparent;
                margin: 0px;
            }

            QScrollBar::handle:vertical {
                background: #B0B0B0;
                min-height: 30px;
                border-radius: 4px;
            }

            QScrollBar::handle:vertical:hover {
                background: #8A8A8A;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }

            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: transparent;
            }

            QScrollBar:horizontal {
                height: 8px;
                background: transparent;
                margin: 0px;
            }

            QScrollBar::handle:horizontal {
                background: #B0B0B0;
                min-width: 30px;
                border-radius: 4px;
            }

            QScrollBar::handle:horizontal:hover {
                background: #8A8A8A;
            }

            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {
                width: 0px;
            }

            QScrollBar::add-page:horizontal,
            QScrollBar::sub-page:horizontal {
                background: transparent;
            }
            """
        )
        self.input_dock = None
        self.output_dock = None

        self.init_ui()

    def on_export_finished(self, success, msg):
        """Main-thread handler for export results."""
        from PySide6.QtWidgets import QMessageBox
        if success:
            QMessageBox.information(self, "Export Complete", msg)
        else:
            QMessageBox.critical(self, "Export Failed", msg)

    def init_ui(self):
        # Docking icons Parent class
        class ClickableSvgWidget(QSvgWidget):
            clicked = Signal()  # Define a custom clicked signal
            def __init__(self, parent=None):
                super().__init__(parent)
                self.setCursor(pointing_hand_cursor())

            def mousePressEvent(self, event):
                if event.button() == Qt.MouseButton.LeftButton:
                    self.clicked.emit()  # Emit the clicked signal on left-click
                super().mousePressEvent(event)

        main_v_layout = QVBoxLayout(self)
        main_v_layout.setContentsMargins(0, 0, 0, 0)
        main_v_layout.setSpacing(0)

        menu_h_layout = QHBoxLayout()
        menu_h_layout.setContentsMargins(0, 0, 0, 0)
        menu_h_layout.setSpacing(0)

        self.menu_bar = QMenuBar(self)
        self.menu_bar.setObjectName("template_page_menu_bar")
        self.menu_bar.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.menu_bar.setFixedHeight(28)
        self.menu_bar.setContentsMargins(0, 0, 0, 0)
        menu_h_layout.addWidget(self.menu_bar)

        # Control buttons
        control_btn_widget = QWidget()
        control_btn_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        control_btn_widget.setObjectName("control_btn_widget")
        control_button_layout = QHBoxLayout(control_btn_widget)
        control_button_layout.setSpacing(10)
        control_button_layout.setContentsMargins(5,5,5,5)

        # Cross-section view control
        self.cross_section_control = ClickableSvgWidget()
        self.cross_section_control.setFixedSize(18, 18)
        self.cross_section_control.load(":/vectors/view_btn/cross_section_active.svg")
        self.cross_section_control.setToolTip("Toggle Cross-Section View")
        self.cross_section_control.clicked.connect(self.cross_section_toggle)
        self.cross_section_active = True
        control_button_layout.addWidget(self.cross_section_control)

        # Top view control
        self.top_view_control = ClickableSvgWidget()
        self.top_view_control.setFixedSize(18, 18)
        self.top_view_control.load(":/vectors/view_btn/top_view_active.svg")
        self.top_view_control.setToolTip("Toggle Top View")
        self.top_view_control.clicked.connect(self.top_view_toggle)
        self.top_view_active = True
        control_button_layout.addWidget(self.top_view_control)

        # Logs Dock Control
        self.log_dock_control = ClickableSvgWidget()
        self.log_dock_control.load(":/vectors/view_btn/logs_dock_inactive.svg")
        self.log_dock_control.setFixedSize(18, 18)
        self.log_dock_control.setToolTip("Toggle Logs Dock")
        self.log_dock_control.clicked.connect(self.logs_dock_toggle)
        self.log_dock_active = False
        control_button_layout.addWidget(self.log_dock_control)

        # 3D Cad Control
        self.cad_3d_control = ClickableSvgWidget()
        self.cad_3d_control.load(":/vectors/view_btn/3d_cad_inactive.svg")
        self.cad_3d_control.setFixedSize(18, 18)
        self.cad_3d_control.setToolTip("Toggle 3D CAD View")
        self.cad_3d_control.clicked.connect(self.cad_3d_view_toggle)
        self.cad_3d_view_active = False
        control_button_layout.addWidget(self.cad_3d_control)

        # Plots Control
        self.plots_control = ClickableSvgWidget()
        self.plots_control.load(":/vectors/view_btn/plots_inactive.svg")
        self.plots_control.setFixedSize(18, 18)
        self.plots_control.setToolTip("Toggle 3D Plots View")
        self.plots_control.clicked.connect(self.plots_view_toggle)
        self.plots_view_active = False
        control_button_layout.addWidget(self.plots_control)

        # Input Dock
        self.input_dock_control = ClickableSvgWidget()
        self.input_dock_control.setFixedSize(18, 18)
        self.input_dock_control.load(":/vectors/view_btn/input_dock_active.svg")
        self.input_dock_control.setToolTip("Toggle Input Dock")
        self.input_dock_control.clicked.connect(self.input_dock_toggle)
        self.input_dock_active = True
        control_button_layout.addWidget(self.input_dock_control)

        self.output_dock_control = ClickableSvgWidget()
        self.output_dock_control.load(":/vectors/view_btn/output_dock_inactive.svg")
        self.output_dock_control.setFixedSize(18, 18)
        self.output_dock_control.setToolTip("Toggle Output Dock")
        self.output_dock_control.clicked.connect(self.output_dock_toggle)
        self.output_dock_active = False
        control_button_layout.addWidget(self.output_dock_control)

        menu_h_layout.addWidget(control_btn_widget)
        main_v_layout.addLayout(menu_h_layout)
        self.create_menu_bar_items()

        self.body_widget = QWidget()
        self.layout = QHBoxLayout(self.body_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.splitter = QSplitter(Qt.Horizontal, self.body_widget)
        self.splitter.setHandleWidth(2)
        self.input_dock = InputDock(backend=self.backend, parent=self)
        input_dock_width = self.input_dock.sizeHint().width()
        self._input_dock_default_width = input_dock_width
        self.splitter.addWidget(self.input_dock)

        self.central_widget = QWidget()
        central_H_layout = QHBoxLayout(self.central_widget)

        # Add dock indicator labels
        self.input_dock_label = InputDockIndicator(parent=self)
        self.input_dock_label.setVisible(False)
        central_H_layout.setContentsMargins(0, 0, 0, 0)
        central_H_layout.setSpacing(0)
        central_H_layout.addWidget(self.input_dock_label, 1)

        central_V_layout = QVBoxLayout()
        central_V_layout.setContentsMargins(0, 0, 0, 0)
        central_V_layout.setSpacing(0)

        # Add Tool bar
        self.tool_bar = ToolBarWidget()
        central_V_layout.addWidget(self.tool_bar)

        # Wire context-sensitive toolbar behaviour (no existing code changed)
        from osdagbridge.desktop.ui.utils.toolbar_controller import ToolBarController
        self.toolbar_ctrl = ToolBarController(self.tool_bar)

        # ----------------- CAD + LOG SPLITTER (ADDED) -----------------

        self.cad_log_splitter = QSplitter(Qt.Vertical)
        self.cad_log_splitter.setHandleWidth(4)
        self.cad_log_splitter.setChildrenCollapsible(False)

        # CAD widget
        self.cad_comp_widget = BridgeDualCADWidget(self)
        self.cad_comp_widget.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding
        )
        self.cad_log_splitter.addWidget(self.cad_comp_widget)

        # from osdagbridge.desktop.ui.cad_3d import CAD3DWindow
        # 3D CAD placeholder (mutually exclusive with dual view + plots)
        self.cad_3d_widget = CAD3DWindow()
        self.cad_3d_widget.setVisible(False)
        self.cad_log_splitter.addWidget(self.cad_3d_widget)

        # Plots placeholder (mutually exclusive with dual view + 3d cad)
        from osdagbridge.desktop.ui.mpl_plot_widget import MplPlotWidget
        self.plots_widget = MplPlotWidget()
        self.plots_widget.setVisible(False)
        self.cad_log_splitter.addWidget(self.plots_widget)

        # Connect engineering scale spinner directly (this is not handled by toolbar controller)
        if hasattr(self.tool_bar, "spin_scale"):
            self.tool_bar.spin_scale.valueChanged.connect(self.plots_widget.set_engineering_scale)

        # Log dock (inside splitter)
        self.logs_dock = LogDock(parent=self)
        self.logs_dock.setVisible(False)
        self.logs_dock.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding
        )
        self.logs_dock.setMinimumHeight(80)
        self.cad_log_splitter.addWidget(self.logs_dock)

        central_V_layout.addWidget(self.cad_log_splitter)

        # --------------------------------------------------------------

        # log text
        self.textEdit = self.logs_dock.log_display

        central_H_layout.addLayout(central_V_layout, 6)

        # Add output dock indicator label
        self.output_dock_label = OutputDockIndicator(parent=self)
        self.output_dock_label.setVisible(True)
        central_H_layout.addWidget(self.output_dock_label, 1)
        self.splitter.addWidget(self.central_widget)

        # root is the greatest level of parent that is the MainWindow
        self.output_dock = OutputDock(backend=self.backend, parent=self)
        self.splitter.addWidget(self.output_dock)
        # self.output_dock.setStyleSheet(self.output_dock.styleSheet())
        self.output_dock.hide()

        self.layout.addWidget(self.splitter)

        total_width = self.width() - self.splitter.contentsMargins().left() - self.splitter.contentsMargins().right()
        target_sizes = [0] * self.splitter.count()
        target_sizes[0] = input_dock_width
        target_sizes[2] = 0
        remaining_width = total_width - input_dock_width
        target_sizes[1] = max(0, remaining_width)
        self.splitter.setSizes(target_sizes)
        self.layout.activate()
        main_v_layout.addWidget(self.body_widget)
        
        # Connect input dock changes to CAD widget for real-time updates
        self.setup_cad_connections()
        
        # Initial CAD update to sync with starting UI values (e.g., footpath=None)
        self.update_cad_from_inputs()

        # Update tool bar visibility based on view rules
        self._update_tool_bar_visibility()

    #-------View-Rules-of-Tool-bar-START----------------------------------------

    def _update_tool_bar_visibility(self):
        """Show/hide tool bar buttons based on rules defined here"""
        if self.cad_3d_view_active or self.plots_view_active:
            self.tool_bar.setVisible(True)
        else:
            self.tool_bar.setVisible(False)

    #-------View-Rules-of-Tool-bar-END----------------------------------------
    
    #-------Common-Design-Save-Additional-Inputs-Functionality-START-------

    def _get_additional_inputs(self) -> AdditionalInputs:
        """
        The dialog is constructed exactly once and reused (To make the ui faster).
        """
        
        if self._additional_inputs_dialog is None:
            self._additional_inputs_dialog = AdditionalInputs()
            # This make the dialog modal to the main window,
            # so that user can not interact with the main window when the dialog is open
            self._additional_inputs_dialog.setWindowModality(Qt.ApplicationModal)
            self._additional_inputs_dialog.update_template_page_2d_cad.connect(self.update_2d_cad)

        return self._additional_inputs_dialog
    
    def update_2d_cad(self, cad_state: dict):
        """
        This Function is the connector to the Signal from Additional Inputs when clicked on Save Button
        This updates the 2D CAD using cad state of Typical section cad
        """
        if self._additional_inputs_dialog is not None:

            # This is updated directly because 
            # there is some mapping that takes place in BridgeDualCADWidget which can worst the things
            self.cad_comp_widget.cross_section_widget.update_params(cad_state)

    def _show_additional_inputs(self, target_tab: str | None = None):
        """
        Sync live state into the dialog, then show it.
        Called from common_design_func and from input_dock._on_design_mode_changed.
        """
        dlg = self._get_additional_inputs()

        # Optionally jump to a specific tab
        if target_tab:
            try:
                for i in range(dlg.tabs.count()):
                    if dlg.tabs.tabText(i).strip().lower() == target_tab.lower():
                        dlg.tabs.setCurrentIndex(i)
                        break
            except Exception:
                pass

        # To Update the Input Dictionary before opening it
        dlg.set_input_dictionary(self.input_dict)

        # Update Internal 2D CAD State
        # Single Source of Truth = _last_mapped_params dict in BridgeDualCADWidget
        dlg._update_additional_input_cad()

        # Sync design mode to additional_inputs
        if self.input_dock:
            print(f"\n@@ Syncing design mode to Additional Inputs: {self.input_dock._current_design_mode}")
            dlg.design_mode_trigger(self.input_dock._current_design_mode)


        dlg.show()
        dlg.raise_()
        dlg.activateWindow()

    def validate_required_inputs(self):
        """Check that all required fields have values before allowing design to proceed."""
        required_field_keys = []

        # Collect empty field keys
        for tupple in self.backend.input_values():
            key, label, _, _, _, _, meta_data = tupple
            if meta_data.get("required", False):
                required_field_keys.append((key, label))

        empty_widgets = []
        # collect empty required widgets
        for key, label in required_field_keys:
            widget = self.input_dock.input_widget.findChild(QWidget, key)
            # print(f"[DEBUG] Validating required field '{key}' with widget: {widget}")
            # Do check for QLineEdit
            # Since QComboBox always has a value (the first option)
            if isinstance(widget, QLineEdit):
                if widget.text().strip() == "":
                    empty_widgets.append((widget, label))
            # This is for other options like Project Locations which is to be checked in self.input_dict
            elif not isinstance(widget, QComboBox):
                value = self.input_dict.get(key)
                if value in [None, "", [], {}]:  # Check for empty values
                    empty_widgets.append((widget, label))
        
        # If empty widgets, show error popup and color the fields red
        message = "Please fill in the required(*) fields before proceeding:\n"
        if empty_widgets:
            for widget, label in empty_widgets:
                # Collecting label name to show in popup message
                message += " - " + label.replace('\n', ' ') + "\n"  # Replace \n with space for better readability
                # Highlight widget with red color
                widget.setProperty("error", True)
                widget.style().unpolish(widget)
                widget.style().polish(widget)
            
            # Show error popup
            CustomMessageBox(
                title="Empty Required Fields",
                text=message,
                dialogType=MessageBoxType.Critical
            ).exec()
            return False  # Validation failed
        return True  # Validation passed
    
    def _start_loading(self):
        """Start loading popup"""
        # Install global input blocker filter on QApplication instance to shield CustomWindow
        self._blocker_filter = InputBlockerFilter(self)
        QApplication.instance().installEventFilter(self._blocker_filter)
        
        self.loading = LoadingDialogManager()
        self.loading.show()
        QApplication.processEvents()
        
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        if hasattr(self, 'input_dock') and self.input_dock is not None:
            self.input_dock.setEnabled(False)
        
        def _loading_cb(msg: str, level: str) -> None:
            # stdout_print goes to the log dock only; keep the loading popup clean
            if level == "stdout_print":
                return
            self.loading.send_message(msg, level)
            if self.loading.is_cancelled():
                bridge_logger.cancel()

        # Register the signal relay (not the widget-touching callback) with
        # bridge_logger: logger calls arrive on the design worker thread, and the
        # queued signal marshals them onto the GUI thread before _loading_cb runs.
        self._loading_cb = _loading_cb
        self._logger_relay = self.logger_message.emit
        self.logger_message.connect(self._loading_cb)
        self._cancel_poller = self.loading.is_cancelled
        bridge_logger.add_callback(self._logger_relay)
        bridge_logger.add_cancel_poller(self._cancel_poller)
      
    
    def _finish_loading(self):
        """Close the loading dialog box"""
        # Uninstall input blocker filter
        if hasattr(self, '_blocker_filter') and self._blocker_filter is not None:
            try:
                QApplication.instance().removeEventFilter(self._blocker_filter)
            except Exception:
                pass
            self._blocker_filter = None
            
        try:
            if hasattr(self, 'loading') and self.loading is not None:
                if hasattr(self, '_cancel_poller') and self._cancel_poller is not None:
                    bridge_logger.remove_cancel_poller(self._cancel_poller)
                    self._cancel_poller = None
                self.loading.hide()
            if hasattr(self, '_logger_relay') and self._logger_relay is not None:
                bridge_logger.remove_callback(self._logger_relay)
                self._logger_relay = None
            if hasattr(self, '_loading_cb') and self._loading_cb is not None:
                try:
                    self.logger_message.disconnect(self._loading_cb)
                except Exception:
                    pass
                self._loading_cb = None
            if hasattr(self, 'logs_dock') and self.logs_dock is not None:
                try:
                    self.logs_dock.log_window_title.setText("Log Window")
                except Exception:
                    pass
        finally:
            QApplication.restoreOverrideCursor()
            if hasattr(self, 'input_dock') and self.input_dock is not None:
                self.input_dock.setEnabled(True)

    def common_design_func(self, trigger: str, target_tab: str = None):
        """
        Trigger belongs to one of ["Design", "Save", "Additional Inputs"]
        """
        # print(f"[DEBUG]plot:{self.plots_view_active}")
        # print(f"[DEBUG]3d:{self.cad_3d_view_active}")
        # print(f"[DEBUG]top:{self.top_view_active}")
        # print(f"[DEBUG]c/s:{self.cross_section_active}")
        from pprint import pprint
        self.input_dock._prime_material_inputs()
        print("\n@@input_dictionary_before (common_design_func):\n")
        pprint(self.input_dict)
        # Check required fields
        required_widget_validated = self.validate_required_inputs()
        if not required_widget_validated:
            return                 # Stop design process if validation fails

        # Redefine additional input defaults if required fields changed
        # Solve bridge layout so the dict has computed values before Design or Additional Inputs
        if self.input_dock.is_require_field_changed:
            solve_extend_basic_input_dict(self.input_dict)
            self.input_dock.is_require_field_changed = False

        print("\n@@input_dictionary_after (common_design_func):\n")
        pprint(self.input_dict)

        if trigger == "Design":
            import sys
            import traceback

            # Ignore Design clicks while a run is already in flight.
            if getattr(self, "_design_running", False):
                return
            self._design_running = True

            self._start_loading()

            # Redirect stdout on the main thread before the worker starts; the
            # worker's prints are marshalled to the log via bridge_logger.
            original_stdout = sys.stdout
            sys.stdout = LoggerStdoutRedirector(
                lambda msg: bridge_logger._emit(f"[{bridge_logger._ts()}]   {msg}", "stdout_print"),
                original_stdout,
            )
            self._design_original_stdout = original_stdout

            backend = self.backend
            input_dict = self.input_dict

            # Run the analysis/design pipeline on a worker thread so the Qt event
            # loop stays responsive; all UI wiring happens on the main thread in
            # _on_design_done (queued signal).
            class _DesignWorker(QObject):
                finished = Signal(object, str, bool)  # (exception, traceback, cancelled)

                def run(self):
                    exc_obj, err_trace, cancelled = None, "", False
                    try:
                        backend.set_input(input_dict)
                        backend.design()
                    except RuntimeError as exc:
                        if "cancelled" in str(exc).lower():
                            cancelled = True
                        else:
                            exc_obj, err_trace = exc, traceback.format_exc()
                    except Exception as exc:
                        exc_obj, err_trace = exc, traceback.format_exc()
                    self.finished.emit(exc_obj, err_trace, cancelled)

            self._design_thread = QThread(self)
            self._design_worker = _DesignWorker()
            self._design_worker.moveToThread(self._design_thread)
            self._design_thread.started.connect(self._design_worker.run)
            self._design_worker.finished.connect(self._on_design_done)
            self._design_worker.finished.connect(self._design_thread.quit)
            self._design_thread.finished.connect(self._design_worker.deleteLater)
            self._design_thread.finished.connect(self._design_thread.deleteLater)
            self._design_thread.start()
            return

        if trigger == "Save":
            self.saveOSI_inputs()
            return
        
        elif trigger == "Additional Inputs":
            self._show_additional_inputs(target_tab=target_tab)

    def _on_design_done(self, exc_obj, err_trace, cancelled):
        """Main-thread completion handler for the background design run."""
        import sys
        import traceback

        # Worker is done printing; restore the real stdout.
        if getattr(self, "_design_original_stdout", None) is not None:
            sys.stdout = self._design_original_stdout
            self._design_original_stdout = None
        self._design_running = False

        try:
            if cancelled:
                bridge_logger.warning("Analysis was stopped by the user.")
            elif isinstance(exc_obj, RuntimeError):
                bridge_logger.error(f"Analysis failed: {exc_obj}")
            elif exc_obj is not None:
                self._show_design_error(err_trace)
            else:
                try:
                    self.output_dock.refresh_loadcase_dropdowns()
                    self.output_dock.refresh_member_dropdown()
                    self.output_dock.connect_design_dropdowns()
                    self.output_dock._on_design_selection_changed()
                    # Lock the input dock after design is triggered
                    if self.input_dock and not self.input_dock.is_locked:
                        self.input_dock.toggle_lock()

                    # Wire up the plots widget with results from the completed analysis
                    ds_all    = self.backend.get_results_dataset()
                    loadcases = self.backend.get_available_loadcases()
                    nodes, members = self.backend.get_nodes_members()
                    edge_dist = self.backend.get_edge_dist()
                    self.plots_widget.setup(ds_all, loadcases, nodes, members, edge_dist=edge_dist)
                    self.plots_widget.link_output_dock(self.output_dock)

                    # Render 3D cad using the parameters from Backend
                    self.cad_3d_widget.render_3d_cad(self.backend.get_3d_cad_parameters())
                except Exception:
                    self._show_design_error(traceback.format_exc())
        finally:
            self._finish_loading()

        if not cancelled:
            # Focus 3D-Cad widget
            self.cad_3d_view_toggle(force_show=True)

    def _show_design_error(self, err_trace):
        """Log a design failure and surface it to the user (main thread only)."""
        bridge_logger.error(f"[Design Error]\n{err_trace}")
        self._finish_loading()
        if self.input_dock and self.input_dock.is_locked:
            self.input_dock.toggle_lock(confirm=False)
        lines = [l for l in err_trace.splitlines() if l.strip()]
        short_summary = "\n".join(lines[-2:]) if len(lines) >= 2 else err_trace
        CustomMessageBox(
            title="Design Error",
            text=(
                "An error occurred during design. Please check your inputs and try again.\n\n"
                f"{short_summary}"
            ),
            informativeText=f"Full traceback:\n{err_trace}",
            dialogType=MessageBoxType.Critical,
        ).exec()

    #-------Common-Design-Save-Additional-Inputs-Functionality-END---------

    def setup_cad_connections(self):
        """Connect input dock field changes to CAD widget for real-time updates"""
        # Connect to input dock's value changed signals
        # This will update the CAD whenever any input field changes
        if hasattr(self.input_dock, 'input_value_changed'):
            self.input_dock.input_value_changed.connect(self.update_cad_from_inputs)        
            
    # Function for saving input dictionary into an OSI file
    def saveOSI_inputs(self):
        # Populate additional input defaults so they appear in the saved file
        # even if the user never opened the Additional Inputs dialog.
        try:
            solve_extend_basic_input_dict(self.input_dict)
        except Exception:
            pass

        default_dir = os.path.join(get_documents_folder(), "inputs.osi")
        filePath, _ = QFileDialog.getSaveFileName(self,
                "Save Design Inputs",
                default_dir,
                "Input Files(*.osi)",
                None)
        if not filePath:
            return

        try:
            with open(filePath, 'w') as input_file:
                yaml.dump(self.input_dict, input_file)

            CustomMessageBox(
                title="Success",
                text="Saved OSI Successfully!",
                dialogType=MessageBoxType.Success
            ).exec()

        except Exception as e:
            CustomMessageBox(
                title="Unsaved File",
                text=f"OSI file not saved:\n{e}",
                dialogType=MessageBoxType.Warning
            ).exec()

    def loadOSI_inputs(self):
        filePath, _ = QFileDialog.getOpenFileName(
            self,
            "Load Design Inputs",
            get_documents_folder(),
            "Input Files (*.osi)",
        )
        if not filePath:
            return

        try:
            with open(filePath, "r") as f:
                data = yaml.safe_load(f)

            if not isinstance(data, dict):
                raise ValueError("File does not contain a valid input dictionary.")

            # Reject hand-edited files with invalid values (e.g. span: abcd)
            # before they are populated into the UI, so a bad OSI file cannot
            # silently lead to a failed design.
            validation = validate_osi_inputs(data)
            if not validation.is_valid:
                CustomMessageBox(
                    title="Invalid OSI File",
                    text=(
                        "The OSI file contains invalid values and was not loaded:\n\n"
                        f"{validation.error_text(limit=10)}"
                    ),
                    dialogType=MessageBoxType.Warning
                ).exec()
                return

            self.input_dock.populate_from_dict(data)

            # Sync additional inputs dialog if it has already been constructed
            if self._additional_inputs_dialog is not None:
                self._additional_inputs_dialog.set_input_dictionary(self.input_dict)

            # Refresh 2D CAD to reflect loaded values
            try:
                solve_extend_basic_input_dict(self.input_dict)
                self.cad_comp_widget.update_from_osdag_inputs(self.input_dict)
            except Exception:
                pass

            CustomMessageBox(
                title="Success",
                text="Loaded OSI Successfully!",
                dialogType=MessageBoxType.Success
            ).exec()

        except Exception as e:
            CustomMessageBox(
                title="Error",
                text=f"Could not load OSI file:\n{e}",
                dialogType=MessageBoxType.Warning
            ).exec()

    def update_cad_from_inputs(self):
        """
        Collect inputs from InputDock and update 2D-CAD
        """
        if not self.input_dock:
            return

        # Keep CAD numeric labels in sync with homepage edits by re-solving
        # derived layout values (girders/spacing/overhang/overall width) on-demand.
        if self.input_dock.is_require_field_changed:
            try:
                solve_extend_basic_input_dict(self.input_dict)
                self.input_dock.is_require_field_changed = False
            except Exception:
                # If solver fails mid-edit, keep raw values for best-effort redraw.
                pass

        # Apply state to CAD UI & Update Cad-State
        self.cad_comp_widget.update_from_osdag_inputs(self.input_dict)

    #---------------------------------Docking-Icons-Functionality-START----------------------------------------------

    def input_dock_toggle(self):
        self.input_dock.toggle_input_dock()
        
    def output_dock_toggle(self):
        self.output_dock.toggle_output_dock()

    def cross_section_toggle(self):
        # If 3D CAD or Plots is active, restore dual view instead of toggling
        if self.cad_3d_view_active or self.plots_view_active:
            # Deactivate 3D CAD & update icon
            self.cad_3d_view_active = False
            self.cad_3d_control.load(":/vectors/view_btn/3d_cad_inactive.svg")
            # Deactivate Plots & update icon
            self.plots_view_active = False
            self.plots_control.load(":/vectors/view_btn/plots_inactive.svg")
            # Restore Cross Section as active & update icon
            self.cross_section_active = True
            self.cross_section_control.load(":/vectors/view_btn/cross_section_active.svg")
            # Restore Top View as active & update icon
            self.top_view_active = True
            self.top_view_control.load(":/vectors/view_btn/top_view_active.svg")
            # Switch central area back to dual view widget
            self._set_central_view('dual')
            # Explicitly show both sub-views inside BridgeDualCADWidget
            # (they were hidden when the competing view was activated)
            self.cad_comp_widget.set_cross_section_visible(True)
            self.cad_comp_widget.set_top_view_visible(True)
            return

        # Normal toggle within dual view
        self.cross_section_active = not self.cross_section_active
        if self.cross_section_active:
            self.cross_section_control.load(":/vectors/view_btn/cross_section_active.svg")
        else:
            self.cross_section_control.load(":/vectors/view_btn/cross_section_inactive.svg")
        self.cad_comp_widget.set_cross_section_visible(self.cross_section_active)


    def top_view_toggle(self):
        # If 3D CAD or Plots is active, restore dual view instead of toggling
        if self.cad_3d_view_active or self.plots_view_active:
            # Deactivate 3D CAD & update icon
            self.cad_3d_view_active = False
            self.cad_3d_control.load(":/vectors/view_btn/3d_cad_inactive.svg")
            # Deactivate Plots & update icon
            self.plots_view_active = False
            self.plots_control.load(":/vectors/view_btn/plots_inactive.svg")
            # Restore Top View as active & update icon
            self.top_view_active = True
            self.top_view_control.load(":/vectors/view_btn/top_view_active.svg")
            # Restore Cross Section as active & update icon
            self.cross_section_active = True
            self.cross_section_control.load(":/vectors/view_btn/cross_section_active.svg")
            # Switch central area back to dual view widget
            self._set_central_view('dual')
            # Explicitly show both sub-views inside BridgeDualCADWidget
            # (they were hidden when the competing view was activated)
            self.cad_comp_widget.set_cross_section_visible(True)
            self.cad_comp_widget.set_top_view_visible(True)
            return

        # Normal toggle within dual view
        self.top_view_active = not self.top_view_active
        if self.top_view_active:
            self.top_view_control.load(":/vectors/view_btn/top_view_active.svg")
        else:
            self.top_view_control.load(":/vectors/view_btn/top_view_inactive.svg")
        self.cad_comp_widget.set_top_view_visible(self.top_view_active)


    def cad_3d_view_toggle(self, force_show=False):
        if force_show:
            self.cad_3d_view_active = True
        else:
            self.cad_3d_view_active = not self.cad_3d_view_active

        if self.cad_3d_view_active or force_show:
            # 3D CAD is mutually exclusive — deactivate Plots & update icon
            self.plots_view_active = False
            self.plots_control.load(":/vectors/view_btn/plots_inactive.svg")
            # Hide dual sub-views & update icons
            self.cross_section_active = False
            self.cross_section_control.load(":/vectors/view_btn/cross_section_inactive.svg")
            self.top_view_active = False
            self.top_view_control.load(":/vectors/view_btn/top_view_inactive.svg")
            # Mark 3D CAD as active & update icon
            self.cad_3d_control.load(":/vectors/view_btn/3d_cad_active.svg")
            # Switch central area to 3D CAD widget
            self._set_central_view('3d')
        else:
            # 3D CAD turned off — mark inactive & update icon
            self.cad_3d_control.load(":/vectors/view_btn/3d_cad_inactive.svg")
            # Restore dual view button states & update icons
            self.cross_section_active = True
            self.top_view_active = True
            self.cross_section_control.load(":/vectors/view_btn/cross_section_active.svg")
            self.top_view_control.load(":/vectors/view_btn/top_view_active.svg")
            # Switch central area back to dual view widget
            # widget has a real height when splitter sizes are calculated
            self._set_central_view('dual')
            # Explicitly show both sub-views inside BridgeDualCADWidget
            self.cad_comp_widget.set_cross_section_visible(True)
            self.cad_comp_widget.set_top_view_visible(True)


    def plots_view_toggle(self):
        self.plots_view_active = not self.plots_view_active

        if self.plots_view_active:
            # Plots is mutually exclusive — deactivate 3D CAD & update icon
            self.cad_3d_view_active = False
            self.cad_3d_control.load(":/vectors/view_btn/3d_cad_inactive.svg")
            # Hide dual sub-views & update icons
            self.cross_section_active = False
            self.cross_section_control.load(":/vectors/view_btn/cross_section_inactive.svg")
            self.top_view_active = False
            self.top_view_control.load(":/vectors/view_btn/top_view_inactive.svg")
            # Mark Plots as active & update icon
            self.plots_control.load(":/vectors/view_btn/plots_active.svg")
            # Switch central area to Plots widget
            self._set_central_view('plots')
        else:
            # Plots turned off — mark inactive & update icon
            self.plots_control.load(":/vectors/view_btn/plots_inactive.svg")
            # Restore dual view button states & update icons
            self.cross_section_active = True
            self.top_view_active = True
            self.cross_section_control.load(":/vectors/view_btn/cross_section_active.svg")
            self.top_view_control.load(":/vectors/view_btn/top_view_active.svg")
            # Switch central area back to dual view widget
            # widget has a real height when splitter sizes are calculated
            self._set_central_view('dual')
            # Explicitly show both sub-views inside BridgeDualCADWidget
            self.cad_comp_widget.set_cross_section_visible(True)
            self.cad_comp_widget.set_top_view_visible(True)


    def logs_dock_toggle(self):
        self.log_dock_active = not self.log_dock_active

        # Re-apply current central view so the vertical splitter ratio
        # (4/5 active view : 1/5 log dock) is recalculated after show/hide
        if self.cad_3d_view_active:
            self._set_central_view('3d')
        elif self.plots_view_active:
            self._set_central_view('plots')
        else:
            self._set_central_view('dual')

        # Show/hide log dock & update icon
        if self.log_dock_active:
            self.logs_dock.show()
            self.log_dock_control.load(":/vectors/view_btn/logs_dock_active.svg")
        else:
            self.logs_dock.hide()
            self.log_dock_control.load(":/vectors/view_btn/logs_dock_inactive.svg")

    # Helper function to show and hide the 3D CAD | Plots | 2D CAD widgets
    def _set_central_view(self, view: str):
        # First, explicitly turn off any active navigation modes in both views
        # This prevents cross-contamination when switching views
        try:
            # Turn off CAD navigation modes
            if hasattr(self.cad_3d_widget, 'component_selector'):
                selector = self.cad_3d_widget.component_selector
                if hasattr(selector, '_on_pan_toggled'):
                    selector._on_pan_toggled(False)
                if hasattr(selector, '_on_rotate_toggled'):
                    selector._on_rotate_toggled(False)
        except:
            pass
            
        try:
            # Turn off Plot navigation modes
            if hasattr(self.plots_widget, '_toggle_pan'):
                self.plots_widget._toggle_pan(False)
            if hasattr(self.plots_widget, '_toggle_rotate'):
                self.plots_widget._toggle_rotate(False)
        except:
            pass

        # Show only the requested widget; hide the other two
        self.cad_comp_widget.setVisible(view == 'dual')
        self.cad_3d_widget.setVisible(view == '3d')
        self.plots_widget.setVisible(view == 'plots')

        # Enforce 4:1 height ratio between active view and log dock
        # Splitter index order: [dual(0), 3d(1), plots(2), logs(3)]
        total  = self.cad_log_splitter.height()
        view_h = int(total * 4 / 5)
        log_h  = total - view_h

        if view == 'dual':
            self.cad_log_splitter.setSizes([view_h, 0, 0, log_h])
            # Reset toolbar when returning to dual view
            self.toolbar_ctrl.reset()
        elif view == '3d':
            self.cad_log_splitter.setSizes([0, view_h, 0, log_h])
            # Bind toolbar to 3D CAD view
            self.toolbar_ctrl.bind_to_cad_3d(self.cad_3d_widget)
        else:  # plots
            self.cad_log_splitter.setSizes([0, 0, view_h, log_h])
            # Bind toolbar to Plots view
            self.toolbar_ctrl.bind_to_plots(self.plots_widget)
        
        # Update tool bar visibility based on view rules
        self._update_tool_bar_visibility()

    def update_docking_icons(self, input_is_active=None, log_is_active=None, output_is_active=None):
            
        if(input_is_active is not None):
            self.input_dock_active = input_is_active
            # Update and save control state
            self.input_dock_active = input_is_active
            if self.input_dock_active:
                self.input_dock_control.load(":/vectors/view_btn/input_dock_active.svg")
            else:
                self.input_dock_control.load(":/vectors/view_btn/input_dock_inactive.svg")
                        
        # Update output dock icon
        if(output_is_active is not None):
            # Update and save control state
            self.output_dock_active = output_is_active
            if self.output_dock_active:
                self.output_dock_control.load(":/vectors/view_btn/output_dock_active.svg")
            else:
                self.output_dock_control.load(":/vectors/view_btn/output_dock_inactive.svg")

        # Update log dock icon
        if(log_is_active is not None):
            self.log_dock_active = log_is_active
            # Update and save control state
            self.logs_dock_active = log_is_active
            if self.log_dock_active:
                self.log_dock_control.load(":/vectors/view_btn/logs_dock_active.svg")
            else:
                self.log_dock_control.load(":/vectors/view_btn/logs_dock_inactive.svg")

    def toggle_animate(self, show: bool, dock: str = 'output', on_finished=None):
        sizes = self.splitter.sizes()
        n = self.splitter.count()
        if dock == 'input':
            dock_index = 0

        elif dock == 'output':
            dock_index = n - 1
        elif dock == 'log':
            self.logs_dock.setVisible(show)
            if on_finished:
                on_finished()
            return
        else:
            print(f"[Error] Invalid dock: {dock}")
            return
        
        dock_widget = self.splitter.widget(dock_index)
        if show:
            dock_widget.show()
        
        self.splitter.setMinimumWidth(0)
        self.splitter.setCollapsible(dock_index, True)
        for i in range(n):
            self.splitter.widget(i).setMinimumWidth(0)
            self.splitter.widget(i).setMaximumWidth(16777215)
        
        target_sizes = sizes[:]
        total_width = self.width() - self.splitter.contentsMargins().left() - self.splitter.contentsMargins().right()
        input_dock = self.splitter.widget(0)
        output_dock = self.splitter.widget(n - 1)
        
        if dock == 'input':
            if show:
                target_sizes[0] = input_dock.sizeHint().width()
                self.input_dock_label.setVisible(False)
            else:
                target_sizes[0] = 0
                self.input_dock_label.setVisible(True)
            target_sizes[2] = sizes[2]
            remaining_width = total_width - target_sizes[0] - target_sizes[2]
            target_sizes[1] = max(0, remaining_width)
        else:
            if show:
                target_sizes[2] = output_dock.sizeHint().width()
                self.output_dock_label.setVisible(False)
            else:
                target_sizes[2] = 0
                self.output_dock_label.setVisible(True)
            target_sizes[0] = sizes[0]
            remaining_width = total_width - target_sizes[0] - target_sizes[2]
            target_sizes[1] = max(0, remaining_width)

        if sizes == target_sizes:
            if not show:
                dock_widget.hide()
            if on_finished:
                on_finished()
            return
        
        def after_anim():
            self.finalize_dock_toggle(show, dock_widget, target_sizes)
            if on_finished:
                on_finished()

        # User requested "one step animation" with "no delay"
        self.animate_splitter_sizes(
            self.splitter,
            sizes,
            target_sizes,
            duration=0,
            on_finished=after_anim
        )

    def animate_splitter_sizes(self, splitter, start_sizes, end_sizes, duration, on_finished=None):
        if duration <= 0:
            # Instant update
            splitter.setSizes(end_sizes)
            splitter.refresh()
            if splitter.parentWidget() and splitter.parentWidget().layout():
                splitter.parentWidget().layout().activate()
            splitter.update()
            if splitter.parentWidget():
                splitter.parentWidget().update()
            self.update()
            for i in range(splitter.count()):
                widget = splitter.widget(i)
                if widget:
                    widget.update()
            
            if on_finished:
                on_finished()
            return

        # Target 60 FPS -> ~16ms interval
        interval = 16
        steps = max(1, duration // interval)
        
        current_step = 0

        def ease_out_quad(t):
            return t * (2 - t)

        def update_step():
            nonlocal current_step
            if current_step <= steps:
                progress = current_step / steps
                # Apply easing
                eased_progress = ease_out_quad(progress)
                
                sizes = [
                    int(start + (end - start) * eased_progress) 
                    for start, end in zip(start_sizes, end_sizes)
                ]
                
                splitter.setSizes(sizes)
                splitter.refresh()
                if splitter.parentWidget() and splitter.parentWidget().layout():
                    splitter.parentWidget().layout().activate()
                splitter.update()
                if splitter.parentWidget():
                    splitter.parentWidget().update()
                self.update()
                for i in range(splitter.count()):
                    widget = splitter.widget(i)
                    if widget:
                        widget.update()
                
                current_step += 1
            else:
                timer.stop()
                if on_finished:
                    on_finished()

        timer = QTimer(self)
        timer.timeout.connect(update_step)
        timer.start(interval)
        self._splitter_anim = timer

    def finalize_dock_toggle(self, show, dock_widget, target_sizes):
        self.splitter.setSizes(target_sizes)
        if not show:
            dock_widget.hide()
        self.splitter.refresh()
        self.splitter.parentWidget().layout().activate()
        self.splitter.update()
        self.splitter.parentWidget().update()
        self.update()
        for i in range(self.splitter.count()):
            self.splitter.widget(i).update()

    #---------------------------------Docking-Icons-Functionality-END----------------------------------------------

    # ── Report Generation ─────────────────────────────────────────────────────

    def open_report_dialog(self, cad_generator=None):
        """
        Show the report options dialog and trigger report
        generation via the backend. All business logic
        is owned by self.backend.generate_design_report().
        This method owns only: dialog, wait cursor, feedback.
        """
        from osdagbridge.desktop.ui.dialogs.report_options \
            import ReportOptionsDialog
        from osdagbridge.desktop.ui.dialogs.custom_messagebox \
            import CustomMessageBox, MessageBoxType
        from PySide6.QtCore import QThread, Signal, QObject
        from PySide6.QtWidgets import QDialog, QApplication
        from PySide6.QtCore import Qt
        import sys, os, traceback

        try:
            dialog = ReportOptionsDialog(parent=self)

            if hasattr(self, '_report_metadata') \
                    and self._report_metadata:
                dialog.project_name.setText(
                    self._report_metadata.get(
                        'project_name', ''))

            if dialog.exec() != QDialog.DialogCode.Accepted:
                return
            if not dialog.request:
                return

            request = dialog.request

            if not hasattr(self, 'backend') \
                    or self.backend is None:
                CustomMessageBox(
                    title="Report Error",
                    text="No design backend available. "
                         "Run design first.",
                    dialogType=MessageBoxType.Critical,
                ).exec()
                return

            backend = self.backend

            # ── Run in background thread ──────────────────
            class _ReportWorker(QObject):
                finished = Signal(object)

                def __init__(self, backend, request,
                             cad_generator, is_preview):
                    super().__init__()
                    self._backend      = backend
                    self._request      = request
                    self._cad_gen      = cad_generator
                    self._is_preview   = is_preview

                def run(self):
                    print("[REPORT-DEBUG] Worker.run() ENTERED")
                    print(f"[REPORT-DEBUG]   backend type = {type(self._backend).__name__}")
                    print(f"[REPORT-DEBUG]   has generate_design_report = {hasattr(self._backend, 'generate_design_report')}")
                    try:
                        result = \
                            self._backend \
                            .generate_design_report(
                                self._request,
                                self._cad_gen,
                                is_preview=self._is_preview,
                            )
                        print(f"[REPORT-DEBUG] generate_design_report returned: {type(result).__name__}")
                    except Exception as exc:
                        import traceback as _tb
                        print(f"[REPORT-DEBUG] EXCEPTION in worker: {exc}")
                        _tb.print_exc()
                        result = exc
                    self.finished.emit(result)

            QApplication.setOverrideCursor(Qt.WaitCursor)

            class SignalCatcher(QObject):
                catch = Signal(object)
            
            self._report_catcher = SignalCatcher()

            def _on_done(result):
                print(f"[REPORT-DEBUG] _on_done called, result type = {type(result).__name__}")
                QApplication.restoreOverrideCursor()

                if isinstance(result, Exception):
                    err = ''.join(
                        traceback.format_exception(
                            type(result), result,
                            result.__traceback__))
                    CustomMessageBox(
                        title="Report Error",
                        text=f"Report generation failed:"
                             f"\n\n{err[:500]}",
                        dialogType=MessageBoxType.Critical,
                    ).exec()
                    return

                self._report_metadata = {
                    'project_name':
                        request.metadata.project_name,
                }

                if result.pdf_path and \
                        os.path.exists(result.pdf_path):
                    if dialog.is_preview:
                        # Attempt to auto-open the PDF
                        try:
                            if sys.platform == "win32":
                                os.startfile(result.pdf_path)
                            elif sys.platform == "darwin":
                                import subprocess
                                subprocess.run(["open", result.pdf_path], check=False)
                            else:
                                import subprocess
                                subprocess.run(["xdg-open", result.pdf_path], check=False)
                            result.opened = True
                        except Exception as e:
                            print(f"[REPORT-DEBUG] Failed to auto-open PDF: {e}")
                            result.opened = False

                        if not getattr(result, 'opened', False):
                            CustomMessageBox(
                                title="PDF Ready",
                                text=f"Could not auto-open PDF."
                                     f"\nOpen manually:\n"
                                     f"{result.pdf_path}",
                                dialogType=
                                    MessageBoxType.Information,
                            ).exec()
                    else:
                        CustomMessageBox(
                            title="Report Generated "
                                  "Successfully",
                            text=f"PDF report saved to:\n"
                                 f"{result.pdf_path}",
                            informativeText=
                                f"TeX source: "
                                f"{result.tex_path or 'N/A'}",
                            dialogType=MessageBoxType.Success,
                        ).exec()
                else:
                    tex_info = (
                        result.tex_path
                        if result.tex_path and
                        os.path.exists(result.tex_path)
                        else 'Not generated'
                    )
                    CustomMessageBox(
                        title="Report Generation Failed",
                        text=(
                            "PDF could not be generated.\n\n"
                            "Possible causes:\n"
                            "• pdflatex not installed\n"
                            "• LaTeX compilation errors\n\n"
                            f"TeX source:\n{tex_info}"
                        ),
                        dialogType=MessageBoxType.Critical,
                    ).exec()

            self._report_thread = QThread()
            self._report_worker = _ReportWorker(
                backend, request, cad_generator, dialog.is_preview)
            self._report_worker.moveToThread(
                self._report_thread)
            
            self._report_catcher.catch.connect(_on_done)
            self._report_worker.finished.connect(self._report_catcher.catch)
            self._report_worker.finished.connect(self._report_thread.quit)
            
            self._report_thread.started.connect(
                self._report_worker.run)
            self._report_thread.start()

        except Exception:
            QApplication.restoreOverrideCursor()
            err = traceback.format_exc()
            try:
                CustomMessageBox(
                    title="Report Error",
                    text=f"Unexpected error:\n\n{err[:500]}",
                    dialogType=MessageBoxType.Critical,
                ).exec()
            except Exception:
                pass

    # ── End Report Generation ─────────────────────────────────────────────────

    def closeEvent(self, event):
        # Refuse to close while the design worker is running: tearing down the
        # window (and with it the OpenSees/OCC state the worker is using) would
        # crash the process. The user can Stop the analysis first.
        if getattr(self, "_design_running", False):
            bridge_logger.warning("Analysis is still running — stop it before closing the window.")
            event.ignore()
            return
        # Ordered CAD teardown before shutdown so pythonocc/PySide6 don't segfault on exit.
        try:
            cad = getattr(self, "cad_3d_widget", None)
            if cad is not None and hasattr(cad, "cleanup"):
                cad.cleanup()
        except Exception:
            pass
        # Release the OpenSeesPy native domain + cached datasets on shutdown (via OpsMemoryGuard).
        try:
            backend = getattr(self, "backend", None)
            if backend is not None and hasattr(backend, "reset"):
                backend.reset()
        except Exception:
            pass
        super().closeEvent(event)

    def resizeEvent(self, event):

        """Override resizeEvent with safety check."""
        # Check if being deleted
        if not self.isVisible() or self.signalsBlocked():
            return
        
        # Check if splitter exists and has children
        try:
            if not hasattr(self, 'splitter') or self.splitter is None:
                return
            if self.splitter.count() < 3:
                return
            
            if self.input_dock.isVisible():
                input_dock_width = self.input_dock.sizeHint().width()
            else:
                input_dock_width = 0
            
            if self.output_dock.isVisible():
                output_dock_width = self.output_dock.sizeHint().width()
            else:
                output_dock_width = 0
            total_width = self.width() - self.splitter.contentsMargins().left() - self.splitter.contentsMargins().right()
            self.splitter.setMinimumWidth(0)
            self.splitter.setCollapsible(0, True)
            self.splitter.setCollapsible(1, True)
            self.splitter.setCollapsible(2, True)
            for i in range(self.splitter.count()):
                self.splitter.widget(i).setMinimumWidth(0)
                self.splitter.widget(i).setMaximumWidth(16777215)
            target_sizes = [0] * self.splitter.count()
            target_sizes[0] = input_dock_width
            target_sizes[2] = output_dock_width
            remaining_width = total_width - input_dock_width - output_dock_width
            target_sizes[1] = max(0, remaining_width)
            self.splitter.setSizes(target_sizes)
            self.splitter.refresh()
            self.body_widget.layout().activate()
            self.splitter.update()
            super().resizeEvent(event)
            
        except (IndexError, RuntimeError, AttributeError):
            # Being deleted, ignore
            return

    def save3DcadImages(self, backend):
        """
        Save 3D Model in various formats: IGS, STEP, STL, BREP
        """
        # Prefer the 3D CAD widget's generator as the source of shapes
        from OCC.Core.STEPControl import STEPControl_Writer, STEPControl_AsIs
        from OCC.Core.Interface import Interface_Static
        from OCC.Core.IFSelect import IFSelect_RetDone
        from OCC.Core.StlAPI import StlAPI_Writer
        from OCC.Core import BRepTools
        from OCC.Core import IGESControl
        

        # Ensure 3D CAD view is currently active / rendered
        if not getattr(self, 'cad_3d_view_active', False):
            CustomMessageBox(
                title="Warning",
                text="3D CAD view is not active. Show the 3D CAD view before exporting.",
                dialogType=MessageBoxType.Warning
            ).exec()
            return

        # Prefer shapes from the CAD widget generator if available
        fuse_model = None
        try:
            if hasattr(self, 'cad_3d_widget') and getattr(self.cad_3d_widget, 'generator', None):
                fuse_model = self.cad_3d_widget.generator.create3Dcad()
               
        except Exception:
            fuse_model = None

        # Fallback: try backend.create3Dcad() if widget didn't provide one
        if fuse_model is None:
            try:
                fuse_model = backend.create3Dcad() if hasattr(backend, 'create3Dcad') else None
            except Exception:
                fuse_model = None

        if fuse_model is None:
            CustomMessageBox(
                title="Warning",
                text="Could not generate 3D model. Please run Design and render the 3D CAD view first.",
                dialogType=MessageBoxType.Warning
            ).exec()
            return

        # Open save dialog
        files_types = "IGS (*.igs);;STEP (*.stp);;STL (*.stl);;IFC (*.ifc);;BREP (*.brep)"
        default_path = get_documents_folder()
        
        filePath, _ = QFileDialog.getSaveFileName(self, 'Export', os.path.join(default_path, "untitled.igs"),
                                                      files_types)
        
        fName = str(filePath)

        if not fName:
            CustomMessageBox(
                title="Warning",
                text="File not saved",
                dialogType=MessageBoxType.Warning
            ).exec()
            return
        

        try:
            file_extension = fName.split(".")[-1].lower()

            if file_extension == 'igs' or file_extension == 'iges':
                IGESControl.IGESControl_Controller().Init()
                iges_writer = IGESControl.IGESControl_Writer()
                iges_writer.AddShape(fuse_model)
                iges_writer.Write(fName)

            elif file_extension == 'brep':
                # BRepTools can write TopoDS shapes directly
                try:
                    BRepTools.Write(fuse_model, fName)
                except Exception:
                    # fallback to breptools namespace if available
                    try:
                        BRepTools.breptools.Write(fuse_model, fName)
                    except Exception as e:
                        raise

            elif file_extension == 'stp' or file_extension == 'step':
                # Initialize the STEP exporter
                step_writer = STEPControl_Writer()
                Interface_Static.SetCVal("write.step.schema", "AP203")
                
                # Transfer shapes and write file
                step_writer.Transfer(fuse_model, STEPControl_AsIs)
                status = step_writer.Write(fName)
                
                if status != IFSelect_RetDone:
                    raise Exception("STEP export failed")

            elif file_extension == 'stl':
                stl_writer = StlAPI_Writer()
                stl_writer.SetASCIIMode(True)
                stl_writer.Write(fuse_model, fName)

            elif file_extension == 'ifc':
                
                _additional = {}
                if self.input_dock:
                    ai_vals = getattr(self.input_dock, "additional_input_values", None) or {}
                    saved_data = getattr(self.input_dock, "_additional_inputs_saved_data", None) or {}
                    _additional = {**saved_data, **ai_vals}

                cad = self.backend.get_ifc_export_parameters(_additional)
                from osdagbridge.core.ifc_export_bridge.export_ifc_handler import PlateGirderIfcExportHandler
                handler = PlateGirderIfcExportHandler(cad, fName)
                handler.export()

            else:
                raise ValueError(f"Unsupported file format: {file_extension}")

            CustomMessageBox(
                title="Success",
                text=f"File Saved Successfully: {fName}",
                dialogType=MessageBoxType.Success
            ).exec()
            
        except Exception as e:
            CustomMessageBox(
                title="Error",
                text=f"Failed to save file: {str(e)}",
                dialogType=MessageBoxType.Critical
            ).exec()

    #Cad-image-export-Start
    def save_cadImages(self, main):
        """Save the rendered 3D CAD model as a raster image."""

        cad_window = getattr(main, "cad_3d_widget", None)
        display = getattr(cad_window, "display", None)

        if display is None:
            CustomMessageBox(
                title="Information",
                text="3D CAD view is not ready. Run Design and open the 3D CAD view before exporting.",
                dialogType=MessageBoxType.About
            ).exec()
            return

        file_types = (
            "PNG (*.png);;"
            "JPEG (*.jpeg *.jpg);;"
            "TIFF (*.tiff *.tif);;"
            "BMP (*.bmp)"
        )

        filePath, _ = QFileDialog.getSaveFileName(
            self,
            "Export CAD Image",
            os.path.join(str(get_documents_folder()), "cad.png"),
            file_types
        )

        if not filePath:
            return

        _, ext = os.path.splitext(filePath)
        ext = ext.lower()

        if ext in [".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"]:
            display.ExportToImage(filePath)
            CustomMessageBox(
                title="Information",
                text="File saved successfully",
                dialogType=MessageBoxType.About
            ).exec()
        else:
            CustomMessageBox(
                title="Error",
                text="Unsupported file format selected",
                dialogType=MessageBoxType.Critical
            ).exec()
    #Cad-image-export-End

    def create_menu_bar_items(self):
        # File Menus
        file_menu = self.menu_bar.addMenu("File")

        load_input_action = QAction("Load Input", self)
        load_input_action.setShortcut(QKeySequence("Ctrl+L"))
        load_input_action.triggered.connect(lambda: self.loadOSI_inputs())
        file_menu.addAction(load_input_action)

        file_menu.addSeparator()

        save_input_action = QAction("Save Input", self)
        save_input_action.setShortcut(QKeySequence("Ctrl+S"))
        save_input_action.triggered.connect(lambda: self.common_design_func("Save"))
        file_menu.addAction(save_input_action)

        save_log_action = QAction("Save Log Messages", self)
        save_log_action.setShortcut(QKeySequence("Alt+M"))
        file_menu.addAction(save_log_action)

        create_report_action = QAction("Create Design Report", self)
        create_report_action.setShortcut(QKeySequence("Alt+C"))
        create_report_action.triggered.connect(lambda _: self.open_report_dialog())
        file_menu.addAction(create_report_action)

        file_menu.addSeparator()

        save_3d_action = QAction("Save 3D Model", self)
        save_3d_action.setShortcut(QKeySequence("Alt+3"))
        save_3d_action.triggered.connect(lambda: self.save3DcadImages(self.backend))
        file_menu.addAction(save_3d_action)

        save_cad_action = QAction("Save CAD Image", self)
        save_cad_action.setShortcut(QKeySequence("Alt+I"))
        save_cad_action.triggered.connect(lambda: self.save_cadImages(self))
        file_menu.addAction(save_cad_action)

        file_menu.addSeparator()

        quit_action = QAction("Quit", self)
        quit_action.setShortcut(QKeySequence("Shift+Q"))
        file_menu.addAction(quit_action)

        graphics_menu = self.menu_bar.addMenu("Graphics")
        zoom_in_action = QAction("Zoom In", self)
        zoom_in_action.setShortcut(QKeySequence("Ctrl+I"))
        graphics_menu.addAction(zoom_in_action)

        zoom_out_action = QAction("Zoom Out", self)
        zoom_out_action.setShortcut(QKeySequence("Ctrl+O"))
        graphics_menu.addAction(zoom_out_action)

        pan_action = QAction("Pan", self)
        pan_action.setShortcut(QKeySequence("Ctrl+P"))
        graphics_menu.addAction(pan_action)

        rotate_3d_action = QAction("Rotate 3D Model", self)
        rotate_3d_action.setShortcut(QKeySequence("Ctrl+R"))
        graphics_menu.addAction(rotate_3d_action)

        graphics_menu.addSeparator()

        front_view_action = QAction("Show Front View", self)
        front_view_action.setShortcut(QKeySequence("Alt+Shift+F"))
        graphics_menu.addAction(front_view_action)
        
        top_view_action = QAction("Show Top View", self)
        top_view_action.setShortcut(QKeySequence("Alt+Shift+T"))
        graphics_menu.addAction(top_view_action)
        
        side_view_action = QAction("Show Side View", self)
        side_view_action.setShortcut(QKeySequence("Alt+Shift+S"))
        graphics_menu.addAction(side_view_action)

        # Database Menu
        database_menu = self.menu_bar.addMenu("Database")

        input_csv_action = QAction("Save Inputs (.csv)", self)
        database_menu.addAction(input_csv_action)

        output_csv_action = QAction("Save Outputs (.csv)", self)
        database_menu.addAction(output_csv_action)

        input_osi_action = QAction("Save Inputs (.osi)", self)
        database_menu.addAction(input_osi_action)

        download_database_menu = database_menu.addMenu("Download Database")

        download_column_action = QAction("Column", self)
        download_database_menu.addAction(download_column_action)

        download_bolt_action = QAction("Beam", self)
        download_database_menu.addAction(download_bolt_action)

        download_weld_action = QAction("Channel", self)
        download_database_menu.addAction(download_weld_action)

        download_angle_action = QAction("Angle", self)
        download_database_menu.addAction(download_angle_action)
        
        database_menu.addSeparator()

        reset_action = QAction("Reset", self)
        reset_action.setShortcut(QKeySequence("Alt+R"))
        database_menu.addAction(reset_action)

        # Help Menu
        help_menu = self.menu_bar.addMenu("Help")

        video_tutorials_action = QAction("Video Tutorials", self)
        help_menu.addAction(video_tutorials_action)

        design_examples_action = QAction("Design Examples", self)
        help_menu.addAction(design_examples_action)

        help_menu.addSeparator()

        ask_question_action = QAction("Ask Us a Question", self)
        help_menu.addAction(ask_question_action)

        about_osdag_action = QAction("About Osdag", self)
        help_menu.addAction(about_osdag_action)

        help_menu.addSeparator()

        check_update_action = QAction("Check For Update", self)
        help_menu.addAction(check_update_action)

    def trigger_ifc_export(self):
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        from osdagbridge.core.ifc_export_bridge.export_ifc_handler import PlateGirderIfcExportHandler

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export IFC Model", "PlateGirderBridge.ifc", "IFC Files (*.ifc)"
        )
        if not file_path:
            return

        # Merge additional-inputs values (crash barrier, median, railing, widths)
        _additional = {}
        if self.input_dock:
            ai_vals = getattr(self.input_dock, "additional_input_values", None) or {}
            saved_data = getattr(self.input_dock, "_additional_inputs_saved_data", None) or {}
            _additional = {**saved_data, **ai_vals}

        try:
            cad = self.backend.get_ifc_export_parameters(_additional)
        except Exception:
            QMessageBox.critical(self, "Export Failed", "Please run Design before exporting IFC.")
            return

        def completion_callback(success, msg):
            self.export_finished.emit(success, msg)

        handler = PlateGirderIfcExportHandler(cad, file_path, completion_callback)
        handler.export_async()
   

class InputDockIndicator(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        # Ensures automatic deletion when closed
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.parent = parent
        self.setObjectName("input_dock_indicator")
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)  # Fixed width, expanding height

        input_layout = QHBoxLayout(self)
        input_layout.setContentsMargins(6,0,0,0)
        input_layout.setSpacing(0)

        self.input_label = QSvgWidget(":/vectors/inputs_label_light.svg")
        input_layout.addWidget(self.input_label)
        self.input_label.setFixedWidth(32)

        self.toggle_strip = QWidget()
        self.toggle_strip.setObjectName("toggle_strip")
        self.toggle_strip.setFixedWidth(6)  # Always visible
        self.toggle_strip.setStyleSheet("background-color: #90AF13;")
        toggle_layout = QVBoxLayout(self.toggle_strip)
        toggle_layout.setContentsMargins(0, 0, 0, 0)
        toggle_layout.setSpacing(0)
        toggle_layout.setAlignment(Qt.AlignVCenter | Qt.AlignRight)  # Align to right for input dock

        self.toggle_btn = QPushButton("❯")  # Right-pointing chevron for input dock
        self.toggle_btn.setFixedSize(6, 60)
        self.toggle_btn.setCursor(pointing_hand_cursor())
        self.toggle_btn.clicked.connect(self.parent.input_dock_toggle)
        self.toggle_btn.setToolTip("Show input panel")
        self.toggle_btn.setObjectName("toggle_strip_button")
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c8408;
                color: white;
                font-size: 12px;
                font-weight: bold;
                padding: 0px;
                border: none;
            }
            QPushButton:hover {
                background-color: #5e7407;
            }
        """)
        toggle_layout.addStretch()
        toggle_layout.addWidget(self.toggle_btn)
        toggle_layout.addStretch()
        input_layout.addWidget(self.toggle_strip)

class OutputDockIndicator(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        # Ensures automatic deletion when closed
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.parent = parent
        self.setObjectName("output_dock_indicator")
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)  # Fixed width, expanding height

        output_layout = QHBoxLayout(self)
        output_layout.setContentsMargins(0,0,0,0)
        output_layout.setSpacing(0)

        self.toggle_strip = QWidget()
        self.toggle_strip.setFixedWidth(6)  # Always visible
        self.toggle_strip.setObjectName("toggle_strip")
        self.toggle_strip.setStyleSheet("background-color: #90AF13;")
        toggle_layout = QVBoxLayout(self.toggle_strip)
        toggle_layout.setContentsMargins(0, 0, 0, 0)
        toggle_layout.setSpacing(0)
        toggle_layout.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

        self.toggle_btn = QPushButton("❮")  # Show state initially
        self.toggle_btn.setCursor(pointing_hand_cursor())
        self.toggle_btn.setFixedSize(6, 60)
        self.toggle_btn.clicked.connect(self.parent.output_dock_toggle)
        self.toggle_btn.setToolTip("Show panel")
        self.toggle_btn.setObjectName("toggle_strip_button")
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c8408;
                color: white;
                font-size: 12px;
                font-weight: bold;
                padding: 0px;
                border: none;
            }
            QPushButton:hover {
                background-color: #5e7407;
            }
        """)
        toggle_layout.addStretch()
        toggle_layout.addWidget(self.toggle_btn)
        toggle_layout.addStretch()
        output_layout.addWidget(self.toggle_strip)

        self.output_label = QSvgWidget(":/vectors/outputs_label_light.svg")
        output_layout.addWidget(self.output_label)
        self.output_label.setFixedWidth(28)


class CentralPlaceholderWidget(QWidget):
    """
    Temporary placeholder for 3D CAD / Plots views.
    Must be removed after CAD and Plot Integration.
    """
    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 18px; color: #90AF13; font-weight: bold;")
        layout.addWidget(label)
        self.setStyleSheet("background-color: #F8FAF0; border: 1px solid #90AF13;")
