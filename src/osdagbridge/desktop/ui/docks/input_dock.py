
from osdagbridge.core.utils.common import KEY_CARRIAGEWAY_WIDTH
import sys
import os
import math
import json
from PySide6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QComboBox, QScrollArea, QLabel,  QLineEdit, QGroupBox, QSizePolicy, QMessageBox,  QDialog, QToolButton, QFrame,
    
)
from PySide6.QtCore import Qt, QRegularExpression, QSize, QTimer, QPoint, QEvent, Signal
from PySide6.QtGui import QPixmap, QDoubleValidator, QRegularExpressionValidator, QIcon, QColor, QBrush
from PySide6.QtSvgWidgets import *
from osdagbridge.core.utils.common import *
from osdagbridge.desktop.ui.dialogs.additional_inputs import AdditionalInputs
from osdagbridge.desktop.ui.utils.custom_buttons import DockCustomButton
from osdagbridge.desktop.ui.dialogs.project_location import ProjectLocationDialog
from osdagbridge.desktop.ui.docks.dock_utils import apply_field_style
from osdagbridge.desktop.ui.dialogs.material_properties import MaterialPropertiesDialog, sync_custom_materials_across_steel_members

from osdagbridge.desktop.ui.utils.custom_titlebar import CustomTitleBar
from osdagbridge.desktop.ui.dialogs.custom_messagebox import CustomMessageBox, MessageBoxType

class NoScrollComboBox(QComboBox):
    def wheelEvent(self, event):
        event.ignore()  

class InputDock(QWidget):
    # Signal emitted when any input value changes
    input_value_changed = Signal()
    MATERIAL_CUSTOM_OPTION = "Custom"
    
    def __init__(self, backend, parent):
        super().__init__()
        self.parent = parent
        self.backend = backend
        self.input_widget = None
        self.structure_type_combo = None
        self.structure_note = None
        self.project_location_combo = None
        self.custom_location_input = None
        self.include_median_combo = None
        self.footpath_combo = None
        self.additional_inputs = None
        self.additional_inputs_widget = None
        self.additional_input_values = {}  # Store values from additional inputs dialog
        self.material_dialog = None
        self.additional_inputs_btn = None
        self.lock_btn = None
        self.scroll_area = None
        self.is_locked = False

        # Saved session snapshots.
        self._basic_inputs_saved_list: list[dict] = []
        self._additional_inputs_saved_list: list[dict] = []
        self._final_inputs_saved_list: list[dict] = []

        # Bottom action buttons (wired in build_left_panel).
        self.save_input_btn = None
        self.design_btn = None
        self.design_mode_combo = None
        self._current_design_mode = "Optimized"
        self._material_custom_fields = {}
        self._material_previous_selection = {}
        self._material_combo_map = {}

        self.setStyleSheet("background: transparent;")
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.left_container = QWidget()

        # Get input fields from backend
        # Prime backend defaults once per session (safe no-op if not implemented).
        try:
            if hasattr(self.backend, "prime_defaults_from_definitions"):
                self.backend.prime_defaults_from_definitions()
        except Exception:
            pass
        input_field_list = self.backend.input_values()

        self.build_left_panel(input_field_list)
        self.main_layout.addWidget(self.left_container)

        self.toggle_strip = QWidget()
        self.toggle_strip.setStyleSheet("background-color: #90AF13;")
        self.toggle_strip.setFixedWidth(6)
        toggle_layout = QVBoxLayout(self.toggle_strip)
        toggle_layout.setContentsMargins(0, 0, 0, 0)
        toggle_layout.setSpacing(0)
        toggle_layout.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

        self.toggle_btn = QPushButton("❮")
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.setFixedSize(6, 60)
        self.toggle_btn.setToolTip("Hide panel")
        self.toggle_btn.clicked.connect(self.toggle_input_dock)
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
        self.main_layout.addWidget(self.toggle_strip)

    def get_validator(self, validator):
        if validator == 'Int Validator':
            return QRegularExpressionValidator(QRegularExpression("^(0|[1-9]\\d*)(\\.\\d+)?$"))
        elif validator == 'Double Validator':
            return QDoubleValidator()
        else:
            return None
    
    def on_structure_type_changed(self, text):
        """Handle structure type combo box changes"""
        if text == "Other":
            if hasattr(self, 'structure_note'):
                self.structure_note.setVisible(True)
        else:
            if hasattr(self, 'structure_note'):
                self.structure_note.setVisible(False)
 
    def show_project_location_dialog(self):
        """Show Project Location selection dialog"""
        dialog = ProjectLocationDialog()
        
        if dialog.exec() == QDialog.Accepted:
            location_data = dialog.get_selected_location()
            if hasattr(self.backend, "set_input_value"):
                self.backend.set_input_value(KEY_PROJECT_LOCATION, location_data)
            

    def eventFilter(self, obj, event):
        if obj == self.scroll_area and event.type() == QEvent.MouseButtonPress:
            if self.is_locked:
                self.show_lock_tooltip()
            return True  
        return super().eventFilter(obj, event)
    
    def clear_force_hover(self):
        if self.lock_btn:
            self.lock_btn.setProperty("forceHover", False)
            self.lock_btn.style().polish(self.lock_btn)
            self.lock_btn.update()

    def show_lock_tooltip(self):
       
        if hasattr(self, 'tooltip_timer') and self.tooltip_timer.isActive():
            self.tooltip_timer.stop()
       
        lock_global_pos = self.lock_btn.mapToGlobal(self.lock_btn.rect().topRight())
        tooltip_pos = lock_global_pos + QPoint(5, 0)
        self.lock_btn.setProperty("forceHover", True)
        self.lock_btn.style().polish(self.lock_btn)
        self.lock_btn.update()
                
        self.lock_btn_tooltip.adjustSize()
        self.lock_btn_tooltip.move(tooltip_pos)
        self.lock_btn_tooltip.show()
        self.lock_btn_tooltip.raise_()
        
        if not hasattr(self, 'tooltip_timer'):
            self.tooltip_timer = QTimer()
            self.tooltip_timer.setSingleShot(True)
            self.tooltip_timer.timeout.connect(self.lock_btn_tooltip.hide)
            self.tooltip_timer.timeout.connect(self.clear_force_hover)
        
        self.tooltip_timer.start(3000)
    
    def toggle_lock(self):            
        self.is_locked = not self.is_locked
        self.lock_btn.setChecked(self.is_locked)
        self.scroll_area.setDisabled(self.is_locked)
        self.update_lock_icon()

    def update_lock_icon(self):
        if self.lock_btn:
            if self.is_locked:
                self.lock_btn.setIcon(QIcon(":/vectors/lock_close.svg"))
            else:
                self.lock_btn.setIcon(QIcon(":/vectors/lock_open.svg"))
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
    
        if self.parent:
            if self.width() == 0:
                if hasattr(self.parent, 'update_docking_icons'):
                    self.parent.update_docking_icons(input_is_active=False)
            elif self.width() > 0:
                if hasattr(self.parent, 'update_docking_icons'):
                    self.parent.update_docking_icons(input_is_active=True)


    def paintEvent(self, event):
        self.update_lock_icon()
        return super().paintEvent(event)
    
    # Collect all the input dock data to update 2D Cad
    def get_all_input_values(self):

        """
        @author: Faizan
        Collect all input dock values needed by the homepage CAD cross-section.
        Merges basic inputs with Additional Inputs dialog values and seeds
        safe defaults for any CAD parameter not yet entered by the user.
        """
        input_values = {}
        
        # Helper function to safely get numeric value
        def get_numeric_value(widget):
            if isinstance(widget, QLineEdit):
                text = widget.text().strip()
                if text:
                    try:
                        return float(text)
                    except ValueError:
                        pass
            elif isinstance(widget, QComboBox):
                text = widget.currentText().strip()
                return text
            return None
        
        # # Collect all the Input Fields
        # for tupple in self.backend.input_values():
        #     if tupple[2] in [TYPE_COMBOBOX, TYPE_TEXTBOX]:
        #         key = tupple[0]
        #         widget = self.input_dock_widget.findChild(QWidget, key)
        #         if widget:
        #             val = get_numeric_value(widget)
        #             if val is not None:
        #                 input_values[key] = val
        #             else:
        #                 if key == KEY_SKEW_ANGLE:
        #                     input_values[key] = 0.0  # Default skew angle
        
        # Hard code temporarily, will genralize after fixing inputdock generalization
        
        
        # Collect span
        widget = self.input_dock_widget.findChild(QWidget, KEY_SPAN)
        val = get_numeric_value(widget)
        if val is not None:
            input_values[KEY_SPAN] = get_numeric_value(widget)
        
        # Collect carriageway width
        widget = self.input_dock_widget.findChild(QWidget, KEY_CARRIAGEWAY_WIDTH)
        val = get_numeric_value(widget)
        if val is not None:
            input_values[KEY_CARRIAGEWAY_WIDTH] = get_numeric_value(widget)
        
        # Collect skew angle
        widget = self.input_dock_widget.findChild(QWidget, KEY_SKEW_ANGLE)
        val = get_numeric_value(widget)
        if val is not None:
            input_values[KEY_SKEW_ANGLE] = get_numeric_value(widget)
        else:
            input_values[KEY_SKEW_ANGLE] = 0.0  # Default
        
        # Collect footpath
        widget = self.input_dock_widget.findChild(QWidget, KEY_FOOTPATH)
        val = get_numeric_value(widget)
        if val is not None:
            input_values[KEY_FOOTPATH] = get_numeric_value(widget)
        
        # Collect median
        widget = self.input_dock_widget.findChild(QWidget, KEY_INCLUDE_MEDIAN)
        val = get_numeric_value(widget)
        if val is not None:
            input_values[KEY_INCLUDE_MEDIAN] = (self.include_median_combo.currentText() == "Yes")
        
        # Add default values for parameters that CAD widget needs
        # These will be overridden by additional inputs if present
        input_values.setdefault(KEY_NO_OF_GIRDERS, 4)
        input_values.setdefault(KEY_GIRDER_SPACING, 2.75)
        input_values.setdefault(KEY_DECK_OVERHANG, 1.0)
        input_values.setdefault(KEY_DECK_THICKNESS, 200)
        input_values.setdefault(KEY_FOOTPATH_WIDTH, 1.5)
        input_values.setdefault(KEY_FOOTPATH_THICKNESS, 200)
        input_values.setdefault(KEY_CROSS_BRACING_SPACING, 3.5)
        input_values.setdefault(KEY_CRASH_BARRIER_WIDTH, 0.5)
        
        # Merge values from Additional Inputs dialog if they exist
        if hasattr(self, 'additional_input_values') and self.additional_input_values:
            input_values.update(self.additional_input_values)

        print(f"input_values: {input_values}")
        
        return input_values
    
    def emit_value_changed(self):
        """
        @author: Faizan
        Emit input_value_changed to trigger a homepage CAD redraw.
        Connected to every basic input field's change signal so the
        cross-section updates instantly on every user edit.
        """
        self.input_value_changed.emit()

    def toggle_input_dock(self):
        parent = self.parent
        if hasattr(parent, 'toggle_animate'):
            is_collapsing = self.width() > 0
            parent.toggle_animate(show=not is_collapsing, dock='input')
        
        self.toggle_btn.setText("❯" if is_collapsing else "❮")
        self.toggle_btn.setToolTip("Show panel" if is_collapsing else "Hide panel")

    def build_left_panel(self, field_list):
        left_layout = QVBoxLayout(self.left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        self.left_panel = QWidget()
        self.left_panel.setStyleSheet("background-color: white;")
        panel_layout = QVBoxLayout(self.left_panel)
        panel_layout.setContentsMargins(15, 10, 15, 10)
        panel_layout.setSpacing(0)

        top_bar = QHBoxLayout()
        top_bar.setSpacing(8)
        top_bar.setContentsMargins(0, 0, 0, 15)
        
        input_dock_btn = QPushButton("Basic Inputs")
        input_dock_btn.setStyleSheet("""
            QPushButton {
                background-color: #90AF13;
                color: white;
                font-weight: bold;
                font-size: 13px;
                border: none;
                border-radius: 4px;
                padding: 7px 20px;
                min-width: 80px;
            }
        """)
        input_dock_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        top_bar.addWidget(input_dock_btn)
        
        self.additional_inputs_btn = QPushButton("Additional Inputs")
        self.additional_inputs_btn.setCursor(Qt.CursorShape.PointingHandCursor)        
        self.additional_inputs_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: black;
                font-weight: bold;
                font-size: 13px;
                border-radius: 5px;
                border: 1px solid black;
                padding: 7px 20px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #90AF13;
                border: 1px solid #90AF13;
                color: white;
            }
            QPushButton:pressed {
                color: black;
                background-color: white;
                border: 1px solid black;
            }
        """)
        self.additional_inputs_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.additional_inputs_btn.clicked.connect(self.show_additional_inputs)
        top_bar.addWidget(self.additional_inputs_btn)           

        self.lock_btn = QPushButton()
        self.lock_btn.setStyleSheet("""
            QPushButton {
                background-color: #f4f4f4;
                border: none;
                padding: 7px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:checked {
                background-color: #FFA500;
            }
            QPushButton:unchecked {
                background-color: #f4f4f4;
            }
            QPushButton:unchecked:hover {
                background-color: #e0e0e0;
            }
            QPushButton:checked:hover {
                background-color: #fa7a02;
            }
        """)
        self.lock_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lock_btn.setObjectName("lock_btn")
        self.lock_btn.setCheckable(True)
        self.lock_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.lock_btn.clicked.connect(self.toggle_lock)
        top_bar.addWidget(self.lock_btn)
        panel_layout.addLayout(top_bar)

        self.lock_btn_tooltip = QLabel("Unlock to Edit")
        self.lock_btn_tooltip.setStyleSheet("""
            QLabel{
                background-color: #f1f1f1;
                color: #000000;
                border: 1px solid #90AF13;
                padding: 4px;
                font-size: 15px;
                border-radius: 0px;
                qproperty-alignment: AlignVCenter;
            }
        """)
        self.lock_btn_tooltip.setObjectName("lock_btn_tooltip")
        self.lock_btn_tooltip.setWindowFlags(Qt.ToolTip)
        self.lock_btn_tooltip.hide()

        scroll_area = QScrollArea()
        self.scroll_area = scroll_area
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        scroll_area.installEventFilter(self)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                padding: 0px 5px;
                border-top: 1px solid #909090;
                border-bottom: 1px solid #909090;
            }

            QScrollArea QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 8px;
                margin-left: 2px;
            }

            QScrollArea QScrollBar::handle:vertical {
                background: #c0c0c0;
                border-radius: 4px;
                min-height: 20px;
            }

            QScrollArea QScrollBar::handle:vertical:hover {
                background: #a0a0a0;
            }

            QScrollArea QScrollBar::handle:vertical:pressed {
                background: #808080;
            }

            QScrollArea QScrollBar::add-line:vertical,
            QScrollArea QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }

            QScrollArea QScrollBar::add-page:vertical,
            QScrollArea QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

        group_container = QWidget()

        # This contains all the dynamically created UI
        self.input_dock_widget = group_container

        self.input_widget = group_container
        group_container_layout = QVBoxLayout(group_container)
        group_container_layout.setContentsMargins(0, 0, 0, 0)
        group_container_layout.setSpacing(12)
        
        self.section_contexts = {}
        self.container_layouts = {}

        self._build_basic_inputs(field_list, group_container_layout)

        group_container_layout.addStretch()
        scroll_area.setWidget(group_container)

        self.data = {}
        panel_layout.addWidget(scroll_area)

        # Bottom buttons
        btn_button_layout = QHBoxLayout()
        btn_button_layout.setContentsMargins(0, 15, 0, 0)
        btn_button_layout.setSpacing(10)

        save_input_btn = DockCustomButton("Save Input", ":/vectors/save.svg")
        save_input_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn_button_layout.addWidget(save_input_btn)

        self.save_input_btn = save_input_btn
        try:
            self.save_input_btn.clicked.connect(self._on_save_input_clicked)
        except Exception:
            pass

        design_btn = DockCustomButton("Design", ":/vectors/design.svg")
        design_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn_button_layout.addWidget(design_btn)

        self.design_btn = design_btn
        try:
            self.design_btn.clicked.connect(self._on_design_clicked)
        except Exception:
            pass

        panel_layout.addLayout(btn_button_layout)

        # Horizontal scroll area
        h_scroll_area = QScrollArea()
        h_scroll_area.setWidgetResizable(True)
        h_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        h_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        h_scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        h_scroll_area.setStyleSheet("""
            QScrollArea{
                background: transparent;
            }
            QScrollBar:horizontal{
                background: #E0E0E0;
                height: 8px;
                margin: 3px 0px 0px 0px;
                border-radius: 2px;
            }
            QScrollBar::handle:horizontal{
                background: #A0A0A0;
                min-width: 30px;
                border-radius: 2px;
            }
            QScrollBar::handle:horizontal:hover{
                background: #707070;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal{
                width: 0px;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal{
                background: none;
            }
        """)
        h_scroll_area.setWidget(self.left_panel)

        left_layout.addWidget(h_scroll_area)
        self._apply_lock_state()

    # -----------------------------
    # Input serialization helpers
    # -----------------------------
    def _sync_basic_widgets_to_backend(self) -> None:
        """Push the latest widget values into backend state.

        Rationale: clicking Design can happen while a QLineEdit still has focus,
        so editingFinished may not have fired yet.
        """
        if not self.backend or not hasattr(self.backend, "set_input_value"):
            return

        # Prefer definition order from backend if available.
        keys = []
        try:
            if hasattr(self.backend, "list_input_keys"):
                keys = list(self.backend.list_input_keys() or [])
        except Exception:
            keys = []

        # Fallback: use all named widgets under the input panel.
        if not keys and getattr(self, "left_panel", None) is not None:
            try:
                for widget in self.left_panel.findChildren((QLineEdit, QComboBox)):
                    name = (widget.objectName() or "").strip()
                    if name:
                        keys.append(name)
            except Exception:
                return

        for key in keys:
            if not isinstance(key, str) or not key:
                continue
            widget = None
            try:
                widget = self.left_panel.findChild(QWidget, key) if getattr(self, "left_panel", None) is not None else None
            except Exception:
                widget = None

            try:
                if isinstance(widget, QLineEdit):
                    self.backend.set_input_value(key, widget.text().strip())
                elif isinstance(widget, QComboBox):
                    self.backend.set_input_value(key, widget.currentText())
            except Exception:
                continue

    def _collect_basic_inputs_list(self) -> list[dict]:
        self._sync_basic_widgets_to_backend()
        try:
            if hasattr(self.backend, "export_basic_inputs_as_list"):
                return list(self.backend.export_basic_inputs_as_list(include_empty=False) or [])
        except Exception:
            pass

        # Fallback: best-effort build from backend dict.
        values = {}
        try:
            if hasattr(self.backend, "get_input_values_dict"):
                values = self.backend.get_input_values_dict(include_empty=False) or {}
        except Exception:
            values = {}
        out: list[dict] = []
        for k, v in (values or {}).items():
            if v in (None, ""):
                continue
            out.append({k: v})
        return out

    def _collect_additional_inputs_snapshot(self) -> dict:
        """Return the best available Additional Inputs payload.

        Priority:
        1) Live dialog (even if not yet saved),
        2) last saved dialog state from the session,
        3) empty.
        """
        # 1) Live dialog (if open)
        try:
            if self.additional_inputs is not None and hasattr(self.additional_inputs, "section_properties_tab"):
                tab = self.additional_inputs.section_properties_tab
                if tab is not None and hasattr(tab, "save_properties"):
                    live = tab.save_properties() or {}
                    if isinstance(live, dict) and live:
                        return live
        except Exception:
            pass

        # 2) Last saved
        saved = getattr(self, "_additional_inputs_saved_data", None)
        return saved if isinstance(saved, dict) else {}

    def _collect_additional_inputs_list(self) -> list[dict]:
        snapshot = self._collect_additional_inputs_snapshot()
        if not isinstance(snapshot, dict) or not snapshot:
            return []
        out: list[dict] = []
        # Keep order stable for downstream consumers.
        for key in ("girder_details", "stiffener_details", "cross_bracing", "end_diaphragm"):
            if key in snapshot:
                out.append({key: snapshot.get(key)})
        # Include any unknown keys last.
        for key, val in snapshot.items():
            if key in {"girder_details", "stiffener_details", "cross_bracing", "end_diaphragm"}:
                continue
            out.append({key: val})
        return out

    def _collect_final_inputs_list(self) -> list[dict]:
        basic_list = self._collect_basic_inputs_list()
        additional_list = self._collect_additional_inputs_list()
        final_list = list(basic_list) + list(additional_list)
        return final_list

    def _debug_dump_final_inputs(self, final_inputs: list[dict], max_chars: int = 12000) -> None:
        """Developer-oriented dump of the merged inputs.

        Prints to stdout and (if available) appends to the GUI Logs dock.
        Payload is truncated to avoid freezing the UI/terminal.
        """
        try:
            payload = json.dumps(final_inputs, indent=2, ensure_ascii=False, default=str)
        except Exception:
            payload = str(final_inputs)

        truncated = False
        if isinstance(payload, str) and len(payload) > max_chars:
            payload = payload[:max_chars] + f"\n... (truncated, total {len(payload)} chars)"
            truncated = True

        header = (
            f"[OsdagBridge] final_design_inputs prepared: {len(final_inputs)} items"
            + (" (truncated)" if truncated else "")
        )

        try:
            print(header)
            print(payload)
        except Exception:
            pass

        # If the parent page has a Logs dock, mirror the dump there too.
        try:
            log_widget = getattr(self.parent, "textEdit", None)
            if log_widget is not None and hasattr(log_widget, "append"):
                log_widget.append(header)
                # Keep the GUI log smaller than terminal.
                gui_payload = payload if len(payload) <= 4000 else payload[:4000] + "\n... (truncated for GUI log)"
                log_widget.append(gui_payload)
        except Exception:
            pass

    # -----------------------------
    # Button handlers
    # -----------------------------
    def _on_save_input_clicked(self) -> None:
        self._basic_inputs_saved_list = self._collect_basic_inputs_list()
        self._additional_inputs_saved_list = self._collect_additional_inputs_list()
        self._final_inputs_saved_list = list(self._basic_inputs_saved_list) + list(self._additional_inputs_saved_list)

        # Persist to backend for later export (csv/osi) or design execution.
        try:
            if hasattr(self.backend, "set_input_value"):
                self.backend.set_input_value("basic_inputs_list", self._basic_inputs_saved_list)
                self.backend.set_input_value("additional_inputs_list", self._additional_inputs_saved_list)
            if hasattr(self.backend, "set_final_design_inputs"):
                self.backend.set_final_design_inputs(self._final_inputs_saved_list)
        except Exception:
            pass

        QMessageBox.information(
            self,
            "Inputs Saved",
            "Basic + Additional inputs saved for this session.",
        )

    def _on_design_clicked(self) -> None:
        self._final_inputs_saved_list = self._collect_final_inputs_list()

        try:
            if hasattr(self.backend, "set_final_design_inputs"):
                self.backend.set_final_design_inputs(self._final_inputs_saved_list)
            elif hasattr(self.backend, "set_input_value"):
                self.backend.set_input_value("final_design_inputs", self._final_inputs_saved_list)
        except Exception:
            pass

        QMessageBox.information(
            self,
            "Design Input Ready",
            "Final merged input payload is prepared (Basic + Additional).",
        )

        # Option 2: print merged inputs for quick verification.
        self._debug_dump_final_inputs(self._final_inputs_saved_list)
    
    def _show_additional_inputs_dialog(self, target_tab_name=None):
        """
        @author: Faizan
        Create the AdditionalInputs dialog, passing current footpath,
        carriageway width, and live homepage CAD state as initial_cad_state
        so the dialog preview starts in sync with the homepage cross-section.
        Restores previously saved dialog state and connects save_button to
        _update_cad_from_additional_inputs.
        """

        footpath_value = self.footpath_combo.currentText() if self.footpath_combo else "None"
        
        carriageway_width = self._get_effective_carriageway_width()

        # Lazily create the in-session storage for Additional Inputs.
        if not hasattr(self, "_additional_inputs_saved_data"):
            self._additional_inputs_saved_data = {}

        # Grab homepage CAD state so dialog preview starts in sync
        initial_cad_state = {}
        try:
            if hasattr(self.parent, 'cad_comp_widget'):
                initial_cad_state = dict(self.parent.cad_comp_widget.cross_section_widget.params)
        except Exception:
            pass

        dialog = AdditionalInputs(footpath_value, carriageway_width, initial_cad_state=initial_cad_state)
        self.additional_inputs = dialog
        self.additional_inputs_widget = dialog
        
        # Propagate project location data to additional inputs (for Temperature Load etc)
        location_data = self.backend.get_input_value(KEY_PROJECT_LOCATION) if hasattr(self.backend, "get_input_value") else None
        if location_data and hasattr(self.additional_inputs, 'update_project_location'):
            self.additional_inputs.update_project_location(location_data)
        

        # Disable inner tabs based on current Input Dock selections.
        # Railing tab is disabled when no footpath is selected.
        # Median tab is disabled when median is not included.
        include_median = self.include_median_combo.currentText() if self.include_median_combo else "Yes"
        dialog.apply_tab_visibility(footpath_value, include_median)

        # Restore previously saved dialog state (includes stiffener details).
        if isinstance(getattr(self, "_additional_inputs_saved_data", None), dict) and self._additional_inputs_saved_data:
            try:
                dialog.set_properties_data(self._additional_inputs_saved_data)
            except Exception:
                pass

        try:
            dialog.set_member_properties_design_mode(self._get_basic_design_mode())
        except Exception:
            pass

        if target_tab_name:
            try:
                for idx in range(self.additional_inputs.tabs.count()):
                    tab_text = str(self.additional_inputs.tabs.tabText(idx) or "").strip()
                    if tab_text.lower() == str(target_tab_name).strip().lower():
                        self.additional_inputs.tabs.setCurrentIndex(idx)
                        break
            except Exception:
                pass

        # Capture state when dialog closes or Save is clicked.
        try:
            dialog.finished.connect(self._handle_additional_inputs_closed)
            if hasattr(dialog, "save_button"):
                dialog.save_button.clicked.connect(lambda: self._update_cad_from_additional_inputs(dialog))
        except Exception:
            pass

        # Connect to accept signal to handle save
        result = dialog.exec_()
        
        # If user clicked Save (accepted) or closed, trigger final update
        if result == AdditionalInputs.Accepted:
            self._update_cad_from_additional_inputs(dialog)

    def _update_cad_from_additional_inputs(self, dialog):
        """
        @author: Faizan
        Read all values from the Additional Inputs dialog after save, merge
        them into additional_input_values, and emit input_value_changed to
        trigger a homepage CAD redraw with the updated parameters.
        """
        if not dialog:
            return
        values = dialog.get_all_values()
        if values:
            # Merge with existing input values
            self.additional_input_values = values
            # Emit signal to trigger homepage CAD update
            self.input_value_changed.emit()

    def show_additional_inputs(self):
        """Show Additional Inputs dialog with its default initial tab."""
        self._show_additional_inputs_dialog()
    
    def _apply_lock_state(self):
        self.update_lock_icon()

        enabled = not self.is_locked
        if self.scroll_area:
            self.scroll_area.setEnabled(enabled)
        if self.input_widget:
            self.input_widget.setEnabled(enabled)
        self._set_additional_inputs_enabled(enabled)

        if self.material_dialog:
            self.material_dialog.setEnabled(enabled)

    def _set_additional_inputs_enabled(self, enabled):
        if self.additional_inputs_widget:
            self.additional_inputs_widget.setEnabled(enabled)

    def _handle_additional_inputs_closed(self):
        # Persist the last saved Additional Inputs data for the session.
        try:
            if self.additional_inputs is not None and hasattr(self.additional_inputs, "get_saved_data"):
                saved = self.additional_inputs.get_saved_data()
                if isinstance(saved, dict) and saved:
                    self._additional_inputs_saved_data = saved
        except Exception:
            pass
        self.additional_inputs = None
        self.additional_inputs_widget = None

    def _build_basic_inputs(self, field_definitions, root_layout):
        current_section_id = None
        for definition in field_definitions:
            key, label, field_type, values, required, validator, metadata = self._normalize_definition(definition)
            if field_type == TYPE_MODULE:
                continue
            if field_type == TYPE_TITLE:
                section_id = key or label
                section_context = self._create_section_context(section_id, label, metadata, root_layout)
                current_section_id = section_context["id"]
                continue
            if current_section_id is None:
                continue
            section_context = self.section_contexts.get(current_section_id)
            if not section_context:
                continue
            self._create_field_row(section_context, key, label, field_type, values, validator, metadata)

        self._finalize_section_contexts()
        self._update_carriageway_placeholder()
        sync_custom_materials_across_steel_members(self._material_combo_map, self._ensure_material_option)

    def _normalize_definition(self, definition):
        if len(definition) == 6:
            return (*definition, {})
        return definition

    def _create_section_context(self, section_id, title, metadata, root_layout):
        container_key = (metadata or {}).get("container", "main")
        parent_layout = self._get_container_layout(container_key, root_layout, metadata)

        show_title = metadata.get("show_group_title", True) if metadata else True
        group_title = title if show_title and title else ""
        group_box = QGroupBox(group_title) if group_title else QGroupBox()
        group_box.setStyleSheet(self._section_groupbox_style())

        layout = QVBoxLayout(group_box)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        if metadata and metadata.get("custom_content") == "project_location":
            self._add_project_location_controls(layout, metadata)

        parent_layout.addWidget(group_box)
        context = {
            "id": section_id,
            "layout": layout,
            "metadata": metadata or {},
            "group_box": group_box,
        }
        self.section_contexts[section_id] = context
        return context

    def _section_groupbox_style(self):
        return (
            "QGroupBox {\n"
            "    border: 1px solid #90AF13;\n"
            "    border-radius: 4px;\n"
            "    background-color: white;\n"
            "    padding: 8px;\n"
            "    margin-top: 12px;\n"
            "    font-size: 10px;\n"
            "    font-weight: bold;\n"
            "    color: #333;\n"
            "}\n"
            "QGroupBox::title {\n"
            "    subcontrol-origin: margin;\n"
            "    subcontrol-position: top left;\n"
            "    left: 8px;\n"
            "    padding: 0 4px;\n"
            "    margin-top: 4px;\n"
            "    background-color: white;\n"
            "    color: #333;\n"
            "}"
        )

    def _get_container_layout(self, container_key, root_layout, metadata=None):
        if not container_key or container_key == "main":
            return root_layout
        if container_key in self.container_layouts:
            return self.container_layouts[container_key]
        body_layout = self._create_container_group(container_key, root_layout, metadata)
        self.container_layouts[container_key] = body_layout
        return body_layout

    def _container_display_name(self, container_key, metadata):
        if metadata:
            custom = metadata.get("container_label") or metadata.get("container_title")
            if custom:
                return custom
        fallback = container_key or "Section"
        return fallback.replace("_", " ").title()

    def _create_container_group(self, container_key, root_layout, metadata=None):
        display_name = self._container_display_name(container_key, metadata or {})
        group = QGroupBox()
        group.setStyleSheet(
            "QGroupBox {\n"
            "    border: 1px solid #90AF13;\n"
            "    border-radius: 5px;\n"
            "    margin-top: 0px;\n"
            "    padding-top: 5px;\n"
            "    background-color: white;\n"
            "}\n"
        )
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(10, 10, 10, 10)
        container_layout.setSpacing(10)

        header = QHBoxLayout()
        title_label = QLabel(display_name)
        title_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #333;")
        header.addWidget(title_label)
        header.addStretch()

        toggle_btn = QPushButton()
        toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        toggle_btn.setCheckable(True)
        toggle_btn.setChecked(True)
        toggle_btn.setIcon(QIcon(":/vectors/arrow_up_light.svg"))
        toggle_btn.setIconSize(QSize(20, 20))
        toggle_btn.setStyleSheet(
            "QPushButton {\n"
            "    background: transparent;\n"
            "    border: none;\n"
            "    padding: 2px;\n"
            "}\n"
            "QPushButton:hover {\n"
            "    background: transparent;\n"
            "}\n"
            "QPushButton:pressed {\n"
            "    background: transparent;\n"
            "}"
        )
        header.addWidget(toggle_btn)
        container_layout.addLayout(header)

        container_body = QFrame()
        container_body.setFrameShape(QFrame.NoFrame)
        body_layout = QVBoxLayout(container_body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(10)
        container_body.setVisible(True)
        container_layout.addWidget(container_body)

        def _toggle(checked):
            container_body.setVisible(checked)
            icon = ":/vectors/arrow_up_light.svg" if checked else ":/vectors/arrow_down_light.svg"
            toggle_btn.setIcon(QIcon(icon))

        toggle_btn.toggled.connect(_toggle)

        group.setLayout(container_layout)
        root_layout.addWidget(group)
        return body_layout

    def _add_project_location_controls(self, layout, metadata):
        label_text = metadata.get("header_label") or "Project Location*"
        button_rows = metadata.get("button_rows")
        if button_rows:
            for row_entry in button_rows:
                row_config = self._prepare_button_row_config(row_entry, {"label": label_text})
                if row_config:
                    self._add_button_row(layout, row_config)
            return

        fallback_row = self._prepare_button_row_config("project_location", {"label": label_text})
        self._add_button_row(layout, fallback_row)

    def _section_label_style(self):
        return (
            "QLabel {\n"
            "    color: #000000;\n"
            "    font-size: 12px;\n"
            "    background: transparent;\n"
            "}"
        )

    def _default_action_button_style(self):
        return (
            "QPushButton {\n"
            "    background-color: #90AF13;\n"
            "    color: white;\n"
            "    font-weight: bold;\n"
            "    border: none;\n"
            "    border-radius: 4px;\n"
            "    padding: 8px 20px;\n"
            "    font-size: 11px;\n"
            "    min-width: 80px;\n"
            "}\n"
            "QPushButton:hover {\n"
            "    background-color: #7a9a12;\n"
            "}\n"
            "QPushButton:disabled{\n"
            "    background: #D0D0D0;\n"
            "    color: #666;\n"
            "}"
        )

    def _default_row_config(self, row_type):
        mapping = {
            "project_location": {
                "label": "Project Location*",
                "buttons": [
                    {"text": "Add Here", "action": "show_project_location_dialog"},
                ],
            },
            "additional_geometry": {
                "label": "Additional Geometry",
                "buttons": [
                    {"text": "Modify Here", "action": "show_additional_inputs"},
                ],
            },
        }
        return mapping.get(row_type, {})

    def _prepare_button_row_config(self, config_entry, fallback_defaults=None):
        fallback_defaults = fallback_defaults or {}
        if isinstance(config_entry, str):
            config = {"type": config_entry}
        else:
            config = dict(config_entry or {})

        row_type = config.get("type")
        defaults = self._default_row_config(row_type)

        resolved = {}
        resolved.update(defaults)
        resolved.update(fallback_defaults)
        resolved.update(config)

        if not resolved.get("buttons"):
            extra_defaults = self._default_row_config(resolved.get("type"))
            if extra_defaults:
                resolved.setdefault("buttons", extra_defaults.get("buttons"))
                resolved.setdefault("label", extra_defaults.get("label"))

        return resolved if resolved.get("buttons") else None

    def _add_button_row(self, layout, config):
        if not config:
            return

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)

        label_text = config.get("label")
        if label_text:
            field_label = QLabel(label_text)
            field_label.setStyleSheet(self._section_label_style())
            field_label.setMinimumWidth(config.get("label_min_width", 110))
            row.addWidget(field_label)

        buttons = config.get("buttons", [])
        for button_config in buttons:
            button = self._create_action_button(button_config)
            stretch = button_config.get("stretch", 1 if len(buttons) == 1 else 0)
            row.addWidget(button, stretch)

        if config.get("add_stretch", True):
            row.addStretch()

        layout.addLayout(row)

    def _create_action_button(self, config):
        button = QPushButton(config.get("text", "Action"))
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        if config.get("size_policy") == "fixed":
            button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        else:
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        icon_path = config.get("icon")
        if icon_path:
            button.setIcon(QIcon(icon_path))
            icon_size = config.get("icon_size")
            if isinstance(icon_size, (list, tuple)) and len(icon_size) == 2:
                button.setIconSize(QSize(icon_size[0], icon_size[1]))

        style = config.get("style") or self._default_action_button_style()
        button.setStyleSheet(style)

        tooltip = config.get("tooltip")
        if tooltip:
            button.setToolTip(tooltip)

        action_name = config.get("action")
        callback = getattr(self, action_name, None) if action_name else None
        if callable(callback):
            button.clicked.connect(callback)
        else:
            button.setEnabled(False)

        return button

    def _create_field_row(self, section_context, key, label, field_type, values, validator, metadata):
        widget = self._create_input_widget(key, field_type, values, validator, metadata)
        if widget is None:
            return
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        display_label = (metadata or {}).get("label") if metadata else None
        field_label = QLabel(display_label or label)
        field_label.setStyleSheet(self._section_label_style())
        field_label.setMinimumWidth(110)
        row.addWidget(field_label)
        if self._is_material_input_key(key) and isinstance(widget, QComboBox):
            combo_container = QWidget()
            combo_layout = QHBoxLayout(combo_container)
            combo_layout.setContentsMargins(0, 0, 0, 0)
            combo_layout.setSpacing(4)
            combo_layout.addWidget(widget, 1)

            info_btn = QToolButton()
            info_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            info_btn.setToolTip("View material properties")
            info_btn.setAutoRaise(True)
            info_btn.setIcon(QIcon(":/vectors/msg_about.svg"))
            info_btn.setFixedSize(20, 20)
            info_btn.setStyleSheet("QToolButton { border: none; padding: 0px; background: transparent; }")
            if info_btn.icon().isNull():
                info_btn.setText("i")
            info_btn.setToolTip("View selected material properties")
            info_btn.clicked.connect(lambda _checked=False, k=key: self._show_selected_material_info_for_key(k))
            combo_layout.addWidget(info_btn)

            row.addWidget(combo_container, 1)
        else:
            row.addWidget(widget, 1)
        if metadata.get("add_stretch"):
            row.addStretch()
        section_context["layout"].addLayout(row)

    def _create_input_widget(self, key, field_type, values, validator, metadata):
        key_name = key if isinstance(key, str) else None

        if field_type == TYPE_COMBOBOX:
            widget = NoScrollComboBox()
            # Connect instant 2D CAD update
            widget.currentTextChanged.connect(self.emit_value_changed)

            apply_field_style(widget)
            if values:
                items = [str(v) for v in values]
                if self._is_material_input_key(key_name):
                    items = [item for item in items if item != self.MATERIAL_CUSTOM_OPTION]
                    items.append(self.MATERIAL_CUSTOM_OPTION)
                widget.addItems(items)

                for i, text in enumerate(items):
                    # Intentionally disabling other option
                    if text == "Other":
                        widget.setItemData(i, QBrush(QColor("gray")), Qt.ItemDataRole.ForegroundRole)
                        model = widget.model()
                        if hasattr(model, 'item'):
                            item = model.item(i)
                            if item:
                                item.setEnabled(False)

            # Prefer backend-stored value, else metadata default.
            try:
                backend_value = self.backend.get_input_value(key_name) if key_name and hasattr(self.backend, "get_input_value") else None
            except Exception:
                backend_value = None

            default_value = (metadata or {}).get("default")

            init_value = backend_value if backend_value not in (None, "") else default_value
            if init_value not in (None, ""):
                idx = widget.findText(str(init_value))
                if idx < 0 and self._is_material_input_key(key_name):
                    self._ensure_material_option(widget, str(init_value))
                    idx = widget.findText(str(init_value))
                if idx >= 0:
                    widget.setCurrentIndex(idx)

            # Persist changes back into backend.
            if key_name and hasattr(widget, "currentTextChanged"):
                try:
                    widget.currentTextChanged.connect(lambda text, k=key_name: self._push_backend_value(k, text))
                except Exception:
                    pass
        elif field_type == TYPE_TEXTBOX:
            widget = QLineEdit()
            # Connect instant 2D CAD update
            widget.textChanged.connect(self.emit_value_changed)

            apply_field_style(widget)
            validator_instance = self.get_validator(validator)
            if validator_instance:
                widget.setValidator(validator_instance)

            # Restore value from backend if present.
            try:
                backend_value = self.backend.get_input_value(key_name) if key_name and hasattr(self.backend, "get_input_value") else None
            except Exception:
                backend_value = None

            if backend_value not in (None, ""):
                widget.setText(str(backend_value))

            # Persist changes back into backend.
            if key_name:
                try:
                    widget.editingFinished.connect(lambda k=key_name, w=widget: self._push_backend_value(k, w.text()))
                except Exception:
                    pass
        else:
            return None

        if key_name:
            widget.setObjectName(key_name)
        self._register_input_widget(key_name, widget)
        self._apply_field_specific_config(key_name, widget, metadata or {})
        return widget

    def _push_backend_value(self, key: str, value):
        if not key:
            return
        if not self.backend or not hasattr(self.backend, "set_input_value"):
            return
        try:
            self.backend.set_input_value(key, value)
        except Exception:
            pass

    def _register_input_widget(self, key, widget):
        if key == KEY_STRUCTURE_TYPE:
            self.structure_type_combo = widget
        elif key == "Design":
            self.design_mode_combo = widget
        elif key == KEY_SPAN:
            self.span_input = widget
        elif key == KEY_CARRIAGEWAY_WIDTH:
            self.carriageway_input = widget
        elif key == KEY_INCLUDE_MEDIAN:
            self.include_median_combo = widget
        elif key == KEY_FOOTPATH:
            self.footpath_combo = widget
        elif key == KEY_SKEW_ANGLE:
            self.skew_input = widget
        elif key == KEY_GIRDER:
            self.girder_combo = widget
        elif key == KEY_CROSS_BRACING:
            self.cross_bracing_combo = widget
        elif key == KEY_END_DIAPHRAGM:
            self.end_diaphragm_combo = widget
        elif key == KEY_DECK_CONCRETE_GRADE_BASIC:
            self.deck_combo = widget

    def _apply_field_specific_config(self, key, widget, metadata):
        if not key or widget is None:
            return
        if key == KEY_STRUCTURE_TYPE and hasattr(widget, "currentTextChanged"):
            widget.currentTextChanged.connect(self.on_structure_type_changed)
        elif key == KEY_SPAN and isinstance(widget, QLineEdit):
            widget.setValidator(QDoubleValidator(SPAN_MIN, SPAN_MAX, 2))
            widget.setPlaceholderText(f"{SPAN_MIN}-{SPAN_MAX} m")
        elif key == KEY_CARRIAGEWAY_WIDTH and isinstance(widget, QLineEdit):
            widget.setValidator(QDoubleValidator(0.0, 100.0, 2))
            widget.editingFinished.connect(self.validate_carriageway_width)
        elif key == KEY_INCLUDE_MEDIAN and hasattr(widget, "currentTextChanged"):
            widget.currentTextChanged.connect(self.on_include_median_changed)
            default_value = metadata.get("default")
            if default_value:
                idx = widget.findText(default_value)
                if idx >= 0:
                    widget.setCurrentIndex(idx)
        elif key == KEY_FOOTPATH and hasattr(widget, "currentTextChanged"):
            widget.currentTextChanged.connect(self.on_footpath_changed)
            default_value = metadata.get("default")
            if default_value:
                idx = widget.findText(default_value)
                if idx >= 0:
                    widget.setCurrentIndex(idx)
        elif key == KEY_SKEW_ANGLE and isinstance(widget, QLineEdit):
            widget.setValidator(QDoubleValidator(SKEW_ANGLE_MIN, SKEW_ANGLE_MAX, 1))
            widget.setPlaceholderText(f"{SKEW_ANGLE_MIN} - {SKEW_ANGLE_MAX}°")
        elif self._is_material_input_key(key) and isinstance(widget, QComboBox):
            if key == KEY_DECK_CONCRETE_GRADE_BASIC and hasattr(widget, "findText"):
                default_value = metadata.get("default")
                if default_value:
                    idx = widget.findText(default_value)
                    if idx >= 0:
                        widget.setCurrentIndex(idx)
            self._material_combo_map[key] = widget
            current_text = str(widget.currentText() or "").strip()
            if current_text and current_text != self.MATERIAL_CUSTOM_OPTION:
                self._material_previous_selection[key] = current_text
            widget.currentTextChanged.connect(
                lambda text, k=key, w=widget: self._on_material_selection_changed(k, w, text)
            )
        elif key == "Design" and hasattr(widget, "currentTextChanged"):
            widget.currentTextChanged.connect(self._on_design_mode_changed_from_user)
            self._set_design_mode(widget.currentText(), open_member_properties=False)

    def _is_material_input_key(self, key) -> bool:
        return key in {
            KEY_GIRDER,
            KEY_CROSS_BRACING,
            KEY_END_DIAPHRAGM,
            KEY_DECK_CONCRETE_GRADE_BASIC,
        }

    def _material_member_for_key(self, key: str) -> str:
        return "Deck" if key in {KEY_DECK_CONCRETE_GRADE_BASIC, KEY_DECK} else "Girder"

    def _set_combo_text_without_signal(self, combo: QComboBox, text: str) -> None:
        idx = combo.findText(text)
        if idx < 0:
            return
        blocked = combo.blockSignals(True)
        try:
            combo.setCurrentIndex(idx)
        finally:
            combo.blockSignals(blocked)

    def _ensure_material_option(self, combo: QComboBox, material_name: str) -> None:
        name = str(material_name or "").strip()
        if not name or combo.findText(name) >= 0:
            return
        custom_idx = combo.findText(self.MATERIAL_CUSTOM_OPTION)
        insert_at = custom_idx if custom_idx >= 0 else combo.count()
        combo.insertItem(insert_at, name)

    def _first_non_custom_option(self, combo: QComboBox) -> str:
        for idx in range(combo.count()):
            value = str(combo.itemText(idx) or "").strip()
            if value and value != self.MATERIAL_CUSTOM_OPTION:
                return value
        return ""

    def _open_custom_material_dialog_for_key(self, key: str, combo: QComboBox) -> bool:
        member = self._material_member_for_key(key)
        previous_value = self._material_previous_selection.get(key, "")

        # Intentionally not passing parent to preserve original dialog appearance.
        dialog = MaterialPropertiesDialog(read_only=False, selected_material=previous_value, member=member)
        if dialog.exec() != QDialog.Accepted:
            return False

        form_data = getattr(dialog, "form_data", {})
        material_name = str(form_data.get("material", "") or "").strip()
        fields = form_data.get("fields", {})
        if not material_name:
            return False

        self._material_custom_fields[material_name] = dict(fields) if isinstance(fields, dict) else {}
        self._ensure_material_option(combo, material_name)
        if member == "Girder":
            sync_custom_materials_across_steel_members(self._material_combo_map, self._ensure_material_option, material_name)
        self._set_combo_text_without_signal(combo, material_name)
        self._material_previous_selection[key] = material_name
        self._push_backend_value(key, material_name)
        self.emit_value_changed()
        return True

    def _on_material_selection_changed(self, key: str, combo: QComboBox, selected_text: str) -> None:
        selected = str(selected_text or "").strip()
        if not selected:
            return

        if selected == self.MATERIAL_CUSTOM_OPTION:
            accepted = self._open_custom_material_dialog_for_key(key, combo)
            if accepted:
                return
            fallback = self._material_previous_selection.get(key) or self._first_non_custom_option(combo)
            if fallback:
                self._set_combo_text_without_signal(combo, fallback)
                self._push_backend_value(key, fallback)
            return

        self._material_previous_selection[key] = selected

    def _show_selected_material_info_for_key(self, key: str) -> None:
        combo = self._material_combo_map.get(key)
        if combo is None:
            return

        selected_material = str(combo.currentText() or "").strip()
        if not selected_material or selected_material == self.MATERIAL_CUSTOM_OPTION:
            CustomMessageBox(
                title="Material Data Unavailable",
                text="No material selected or custom material details not provided.",
                dialogType=MessageBoxType.Warning
            ).exec()
            return

        member = self._material_member_for_key(key)
        custom_fields = self._material_custom_fields.get(selected_material)
        # Intentionally not passing parent to preserve original dialog appearance.
        dialog = MaterialPropertiesDialog(
            read_only=True,
            selected_material=selected_material,
            member=member,
            custom_fields=custom_fields,
        )
        dialog.exec()

    def _get_basic_design_mode(self) -> str:
        if self.design_mode_combo is not None and hasattr(self.design_mode_combo, "currentText"):
            value = str(self.design_mode_combo.currentText() or "").strip()
            if value:
                return value
        value = str(getattr(self, "_current_design_mode", "") or "").strip()
        return value or "Optimized"

    def _set_design_mode(self, mode_text: str, open_member_properties: bool = False) -> None:
        mode = str(mode_text or "").strip() or "Optimized"
        self._current_design_mode = mode

        if self.additional_inputs is not None:
            try:
                if hasattr(self.additional_inputs, "set_member_properties_design_mode"):
                    self.additional_inputs.set_member_properties_design_mode(mode)
            except Exception:
                pass

        if open_member_properties and mode.lower() in {"custom"}:
            self._show_additional_inputs_dialog("Member Properties")

    def _on_design_mode_changed_from_user(self, mode_text: str) -> None:
        self._set_design_mode(mode_text, open_member_properties=True)

    def _finalize_section_contexts(self):
        for context in self.section_contexts.values():
            metadata = context.get("metadata", {})
            note_config = metadata.get("post_note")
            if note_config:
                self._add_section_note(context, note_config)

            for row_entry in metadata.get("post_rows", []):
                row_config = self._prepare_button_row_config(row_entry)
                if row_config:
                    self._add_button_row(context["layout"], row_config)

    def _add_section_note(self, context, note_config):
        note_label = QLabel(note_config.get("text", ""))
        note_label.setStyleSheet(self._section_label_style())
        note_label.setVisible(False)
        context["layout"].addWidget(note_label)
        attr_name = note_config.get("attr")
        if attr_name:
            setattr(self, attr_name, note_label)

    def on_footpath_changed(self, footpath_value):
        """Update additional inputs when footpath changes"""
        if self.additional_inputs and self.additional_inputs.isVisible():
            if hasattr(self, 'additional_inputs_widget'):
                self.additional_inputs_widget.update_footpath_value(footpath_value)
        # Notify CAD so the homepage cross-section updates immediately
        self.emit_value_changed()

    def on_include_median_changed(self, _value):
        self._update_carriageway_placeholder()
        # Re-validate silently so previously entered values honor the new limits
        self.validate_carriageway_width(show_message=False)

    def _carriageway_limits(self):
        include_median = self._is_median_included()
        min_width = CARRIAGEWAY_WIDTH_MIN_WITH_MEDIAN if include_median else CARRIAGEWAY_WIDTH_MIN
        return min_width, CARRIAGEWAY_WIDTH_MAX_LIMIT

    def _update_carriageway_placeholder(self):
        if not hasattr(self, "carriageway_input") or self.carriageway_input is None:
            return
        min_width, max_width = self._carriageway_limits()
        suffix = " per side" if self._is_median_included() else ""
        self.carriageway_input.setPlaceholderText(f"{min_width:.2f} - {max_width:.1f} m{suffix}")

    def validate_carriageway_width(self, show_message=True):
        if not self.carriageway_input:
            return
        text = self.carriageway_input.text().strip()
        if not text:
            return
        try:
            value = float(text)
        except ValueError:
            self.carriageway_input.clear()
            if show_message:
                QMessageBox.warning(self, "Carriageway Width", "Please enter a numeric carriageway width.")
            return

        min_width, max_width = self._carriageway_limits()
        include_median = self._is_median_included()
        message = None

        if value < min_width:
            if include_median:
                message = "IRC 5 Clause 104.3.1 requires minimum carriageway width on both sides of the median to be at least 7.5 m."
            else:
                message = "IRC 5 Clause 104.3.1 requires minimum carriageway width of 4.25 m."
            value = min_width
        elif value > max_width:
            message = "Software limits carriageway width upto 23.6 m"
            value = max_width

        self.carriageway_input.setText(f"{value:.2f}")
        if message and show_message:
            QMessageBox.warning(self, "Carriageway Width", message)

    def _get_effective_carriageway_width(self):
        min_width, max_width = self._carriageway_limits()
        width = min_width
        if self.carriageway_input and self.carriageway_input.text():
            try:
                width = float(self.carriageway_input.text())
            except ValueError:
                width = min_width
        width = max(min_width, min(width, max_width))
        return width

    def _is_median_included(self):
        if not self.include_median_combo:
            return False
        return self.include_median_combo.currentText().lower() == "yes"
