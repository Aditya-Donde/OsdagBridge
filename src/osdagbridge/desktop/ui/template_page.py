import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QMenuBar, QSplitter, QSizePolicy, QPushButton, QScrollArea, QFrame,
)
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtCore import Qt, QFile, QTextStream, Signal,QTimer
from PySide6.QtGui import QIcon, QAction, QKeySequence

from osdagbridge.desktop.ui.docks.input_dock import InputDock
from osdagbridge.desktop.ui.docks.output_dock import OutputDock
from osdagbridge.desktop.ui.docks.log_dock import LogDock
from osdagbridge.desktop.ui.docks.cad_dual_view import BridgeDualCADWidget
from osdagbridge.desktop.ui.dialogs.additional_inputs import AdditionalInputs

from osdagbridge.core.bridge_types.plate_girder.ui_fields import FrontendData
from osdagbridge.core.bridge_types.plate_girder.defaults import DEFAULTS_DICT
from osdagbridge.core.utils.common import *

class CustomWindow(QWidget):
    def __init__(self, title: str, backend: object, parent=None):
        super().__init__()
        self.parent = parent
        self.backend = backend()

        # Source for all input values.
        # Initialised from DEFAULTS_DICT; updated live as the user edits fields.
        self.input_dict = dict(DEFAULTS_DICT)

        self.setWindowTitle(title)
        self.setStyleSheet(
            """
            QWidget {
                background-color: #ffffff;
                margin: 0px;
                padding: 0px;
            }
            QMenuBar {
                background-color: #F4F4F4;
                color: #000000;
                padding: 0px;
            }
            QMenuBar::item {
                padding: 5px 10px;
                background: transparent;
            }
            QMenuBar::item:selected {
                background: #FFFFFF;
            }
            """
        )
        self.input_dock = None
        self.output_dock = None

        self.init_ui()
        # Central CAD state (single source of truth)
        self.cad_state = {}

    def init_ui(self):
        # Docking icons Parent class
        class ClickableSvgWidget(QSvgWidget):
            clicked = Signal()  # Define a custom clicked signal
            def __init__(self, parent=None):
                super().__init__(parent)
                self.setCursor(Qt.CursorShape.PointingHandCursor)

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

        # Input Dock
        self.input_dock_control = ClickableSvgWidget()
        self.input_dock_control.setFixedSize(18, 18)
        self.input_dock_control.load(":/vectors/view_btn/input_dock_active.svg")
        self.input_dock_control.clicked.connect(self.input_dock_toggle)
        self.input_dock_active = True
        control_button_layout.addWidget(self.input_dock_control)

        # Cross-section view control
        self.cross_section_control = ClickableSvgWidget()
        self.cross_section_control.setFixedSize(18, 18)
        self.cross_section_control.load(":/vectors/view_btn/cross_section_active.svg")
        self.cross_section_control.clicked.connect(self.cross_section_toggle)
        self.cross_section_active = True
        control_button_layout.addWidget(self.cross_section_control)

        # Top view control
        self.top_view_control = ClickableSvgWidget()
        self.top_view_control.setFixedSize(18, 18)
        self.top_view_control.load(":/vectors/view_btn/top_view_active.svg")
        self.top_view_control.clicked.connect(self.top_view_toggle)
        self.top_view_active = True
        control_button_layout.addWidget(self.top_view_control)

        # Logs Dock Control
        self.log_dock_control = ClickableSvgWidget()
        self.log_dock_control.load(":/vectors/view_btn/logs_dock_inactive.svg")
        self.log_dock_control.setFixedSize(18, 18)
        self.log_dock_control.clicked.connect(self.logs_dock_toggle)
        self.log_dock_active = False
        control_button_layout.addWidget(self.log_dock_control)

        # 3D Cad Control
        self.cad_3d_control = ClickableSvgWidget()
        self.cad_3d_control.load(":/vectors/view_btn/3d_cad_inactive.svg")
        self.cad_3d_control.setFixedSize(18, 18)
        self.cad_3d_control.clicked.connect(self.cad_3d_view_toggle)
        self.cad_3d_view_active = False
        control_button_layout.addWidget(self.cad_3d_control)

        # Plots Control
        self.plots_control = ClickableSvgWidget()
        self.plots_control.load(":/vectors/view_btn/plots_inactive.svg")
        self.plots_control.setFixedSize(18, 18)
        self.plots_control.clicked.connect(self.plots_view_toggle)
        self.plots_view_active = False
        control_button_layout.addWidget(self.plots_control)

        self.output_dock_control = ClickableSvgWidget()
        self.output_dock_control.load(":/vectors/view_btn/output_dock_inactive.svg")
        self.output_dock_control.setFixedSize(18, 18)
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

        from osdagbridge.desktop.ui.cad_3d import CAD3DWindow
        # 3D CAD placeholder (mutually exclusive with dual view + plots)
        self.cad_3d_widget = CentralPlaceholderWidget("3D CAD Here")
        self.cad_3d_widget.setVisible(False)
        self.cad_log_splitter.addWidget(self.cad_3d_widget)

        # Plots placeholder (mutually exclusive with dual view + 3d cad)
        self.plots_widget = CentralPlaceholderWidget("Analysis Plots Here")
        self.plots_widget.setVisible(False)
        self.cad_log_splitter.addWidget(self.plots_widget)

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
    
    #-------Common-Design-Save-Additional-Inputs-Functionality-START-------

    def common_design_func(self, trigger: str):
        """
        Trigger belongs to one of ["Design", "Save", "Additional Inputs"]
        """
        print(f"@plot:{self.plots_view_active}")
        print(f"@3d:{self.cad_3d_view_active}")
        print(f"@top:{self.top_view_active}")
        print(f"@c/s:{self.cross_section_active}")
        if trigger == "Design":
            # Collect all the values from input Dock and pass to backend
            self.backend.set_input(self.input_dict)
            print(f"@@input_dictionary: {self.input_dict}")
            self.backend.design()
        elif trigger == "Save":
            # Collect all the values from input Dock and save to osi/csv
            pass
        elif trigger == "Additional Inputs":
            # Show Additional Inputs
            pass

    #-------Common-Design-Save-Additional-Inputs-Functionality-END---------
    
    def setup_cad_connections(self):
        """Connect input dock field changes to CAD widget for real-time updates"""
        # Connect to input dock's value changed signals
        # This will update the CAD whenever any input field changes
        if hasattr(self.input_dock, 'input_value_changed'):
            self.input_dock.input_value_changed.connect(self.update_cad_from_inputs)
            
    def open_additional_inputs(self):
        """
        Open Additional Inputs dialog and route values through CAD interface
        """
        dialog = AdditionalInputs(parent=self)

        if dialog.exec():
            # Get values ONLY (do not update CAD directly)
            values = dialog.get_all_values()

            if values:
                self.update_cad_state("additional_inputs", values)
                
    def update_cad_state(self, source: str, values: dict):
        """
        Central CAD interface (single source of truth)
        source: 'input_dock' | 'additional_inputs'
        """
        if not values:
            return

        # 1. Store state
        self.cad_state.update(values)

        # 2. Apply state to CAD UI ONLY
        if hasattr(self, 'cad_comp_widget'):
            self.cad_comp_widget.update_from_osdag_inputs(self.cad_state)
            
    def update_cad_from_inputs(self):
        """
        Collect inputs from InputDock and send to CAD interface
        """
        if not self.input_dock:
            return

        input_values = self.input_dock.get_all_input_values()

        # print("[DEBUG] Collected input values from InputDock:", input_values)
        
        if not input_values:
            return

        # IMPORTANT: send ONLY to interface
        # self.update_cad_state("input_dock", input_values)


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


    def cad_3d_view_toggle(self):
        self.cad_3d_view_active = not self.cad_3d_view_active

        if self.cad_3d_view_active:
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
        elif view == '3d':
            self.cad_log_splitter.setSizes([0, view_h, 0, log_h])
        else:  # plots
            self.cad_log_splitter.setSizes([0, 0, view_h, log_h])
        
    def _position_log_dock(self):
        """Position log dock at bottom of central widget as overlay (max 1/5 height)"""
        if hasattr(self, 'logs_dock') and hasattr(self, 'cad_comp_widget'):
            cad_geom = self.cad_comp_widget.geometry()
            log_height = min(cad_geom.height() // 5, 200)  # 1/5 of window height, max 200px
            self.logs_dock.setGeometry(
                cad_geom.x(),
                cad_geom.y() + cad_geom.height() - log_height,
                cad_geom.width(),
                log_height
            )

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

    def create_menu_bar_items(self):
        # File Menus
        file_menu = self.menu_bar.addMenu("File")

        load_input_action = QAction("Load Input", self)
        load_input_action.setShortcut(QKeySequence("Ctrl+L"))
        file_menu.addAction(load_input_action)

        file_menu.addSeparator()

        save_input_action = QAction("Save Input", self)
        save_input_action.setShortcut(QKeySequence("Ctrl+S"))
        file_menu.addAction(save_input_action)

        save_log_action = QAction("Save Log Messages", self)
        save_log_action.setShortcut(QKeySequence("Alt+M"))
        file_menu.addAction(save_log_action)

        create_report_action = QAction("Create Design Report", self)
        create_report_action.setShortcut(QKeySequence("Alt+C"))
        file_menu.addAction(create_report_action)

        file_menu.addSeparator()

        save_3d_action = QAction("Save 3D Model", self)
        save_3d_action.setShortcut(QKeySequence("Alt+3"))
        file_menu.addAction(save_3d_action)

        save_cad_action = QAction("Save CAD Image", self)
        save_cad_action.setShortcut(QKeySequence("Alt+I"))
        file_menu.addAction(save_cad_action)

        file_menu.addSeparator()

        quit_action = QAction("Quit", self)
        quit_action.setShortcut(QKeySequence("Shift+Q"))
        file_menu.addAction(quit_action)

        # Edit Menus
        edit_menu = self.menu_bar.addMenu("Edit")

        design_prefs_action = QAction("Additional Inputs", self)
        design_prefs_action.setShortcut(QKeySequence("Alt+P"))
        edit_menu.addAction(design_prefs_action)
        design_prefs_action.triggered.connect(self.open_additional_inputs)


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
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
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
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
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