"""Typical Sections tab module extracted from additional_inputs."""
import math
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QLabel, QScrollArea,
    QSizePolicy, QFrame, QTableWidget, QComboBox, QTableWidgetItem,
)
from PySide6.QtCore import Qt, Signal, QTimer

from osdagbridge.core.bridge_types.plate_girder.bridge_geometry import CrossSectionLayout
from osdagbridge.core.utils.common import *
from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style
from osdagbridge.desktop.ui.dialogs.custom_messagebox import CustomMessageBox, MessageBoxType
from osdagbridge.core.bridge_types.plate_girder.ui_fields_additional_input import TYPICAL_SECTION_SCHEMA
from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.typical_section.common_ui_builder import UIBuilder
from osdagbridge.desktop.cad.irc5_geometry import (
    CrashBarrierGeometry,
    MedianGeometry,
    RailingGeometry,
)

ADDITIONAL_INPUTS_SCROLL_STYLE = """
    QScrollArea { background:transparent; padding:0px 5px; border:none}
    QScrollArea QScrollBar:vertical { border:none; background:#f0f0f0; width:8px; }
    QScrollArea QScrollBar::handle:vertical { background:#c0c0c0; border-radius:4px; min-height:20px; }
    QScrollArea QScrollBar::handle:vertical:hover { background:#a0a0a0; }
    QScrollArea QScrollBar::add-line:vertical,
    QScrollArea QScrollBar::sub-line:vertical { border:none; background:none; }
"""


class TypicalSectionDetailsTab(QWidget):
    """Sub-tab for Typical Section Details inputs"""

    girder_count_changed = Signal(int)
    # ----- Setup & shared helpers ----------------------------------------------

    def __init__(
        self, 
        carriageway_width=7.5, 
        parent=None,
        additional_input_instance=None # This is necessary parameter
    ):
        super().__init__(parent)

        # Maintain a reference to the AdditionalInputs instance to access its methods and dictionary
        self.additional_input_instance = additional_input_instance
        
        self._initial_cad_state = {}
        self.carriageway_width = carriageway_width
        self.updating_fields = False
        self._updating_overall_width_display = False
        self._updating_lane_table = False
        self._lane_cell_signal_connected = False
        # Track last known numeric values to avoid spurious recalculations on text-only edits
        self._last_spacing_value: float | None = None
        self._last_overhang_value: float | None = None
        self._last_girders_value: int | None = None
        self.crash_barrier_count = 2  # Assume two crash barriers at carriageway edges
        self.overall_bridge_width_formula = (
            "OverallBridgeWidth = CrossSectionLayout.total_width = (2 x CarriagewayWidth if Median else CarriagewayWidth) + "
            "2 x CrashBarrierWidth + MedianWidth + (NoOfFootpaths x FootpathWidth) + "
            "(NoOfFootpaths x RailingWidth)"
        )
        self.init_ui()

    def update_internal_cad_state(self, cad_state):
        # Apply homepage CAD state so that 2D-CAD is synced
        self._initial_cad_state = cad_state
        self.cad_preview.update_params(self._initial_cad_state)

    def _find_tab_widget(self, tab_id, widget_id, widget_type=QWidget):
        """Generic findChild across any tab by its schema id."""
        tab = self._tab_widgets.get(tab_id)
        return tab.main_widget.findChild(widget_type, widget_id) if tab else None

    def _find_crash_barrier_widget(self, widget_id, widget_type=QWidget):
        return self._find_tab_widget(KEY_CB_TAB, widget_id, widget_type)

    def _find_median_widget(self, widget_id, widget_type=QWidget):
        return self._find_tab_widget(KEY_MD_TAB, widget_id, widget_type)

    def _find_railing_widget(self, widget_id, widget_type=QWidget):
        return self._find_tab_widget(KEY_RL_TAB, widget_id, widget_type)

    def _find_wearing_widget(self, widget_id, widget_type=QWidget):
        return self._find_tab_widget(KEY_WC_TAB, widget_id, widget_type)

    def _find_lane_widget(self, widget_id, widget_type=QWidget):
        return self._find_tab_widget(KEY_WC_LD_TAB, widget_id, widget_type)

    def style_input_field(self, field):
        apply_field_style(field)

    def style_group_box(self, group_box):
        group_box.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #d0d0d0;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 15px;
                background-color: #f9f9f9;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 10px;
                padding: 0 5px;
                background-color: white;
                color: #4a7ba7;
            }
        """)

    def _create_section_card(self, title):
        card = QFrame()
        card.setObjectName("sectionCard")
        card.setStyleSheet("""
            QFrame#sectionCard {
                background-color: white;
                border: none;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(12)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #000;")
        card_layout.addWidget(title_label)

        return card, card_layout

    def init_ui(self):
        schema = TYPICAL_SECTION_SCHEMA
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(0)

        # ── CAD Preview ───────────────────────────────────────────────────────────
        from osdagbridge.desktop.ui.docks.cad_cross_section import CrossSectionCADWidget
        diagram_widget = QWidget()
        diagram_widget.setStyleSheet("""
            QWidget { background: transparent; border: 1px solid #b0b0b0; border-radius: 8px; }
        """)
        diagram_widget.setMinimumHeight(280)
        diagram_widget.setMaximumHeight(380)
        diagram_layout = QVBoxLayout(diagram_widget)
        diagram_layout.setContentsMargins(5, 5, 5, 5)
        cad_scroll = QScrollArea()
        cad_scroll.setWidgetResizable(True)
        cad_scroll.setFrameShape(QFrame.NoFrame)
        cad_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        cad_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        cad_scroll.setStyleSheet(ADDITIONAL_INPUTS_SCROLL_STYLE)
        self.cad_preview = CrossSectionCADWidget()
        self.cad_preview.scale_factor = 0.65
        self.cad_preview.setMinimumHeight(200)
        cad_scroll.setWidget(self.cad_preview)
        diagram_layout.addWidget(cad_scroll)
        main_layout.addWidget(diagram_widget)
        main_layout.addSpacing(5)

        # ── Input container ───────────────────────────────────────────────────────
        input_container = QWidget()
        input_container.setStyleSheet("QWidget { background-color: white; border: none;}")
        input_layout = QVBoxLayout(input_container)
        input_layout.setContentsMargins(0, 10, 0, 0)
        input_layout.setSpacing(10)

        # ── Primary fields (optional — only if schema has "primary_fields") ───────
        self._tab_widgets = {}
        self.primary_widget = None

        if "primary_fields" in schema:
            self.primary_widget = UIBuilder(
                owner=self,
                schema=schema["primary_fields"],
                card_title="Inputs:",
                main_widget_object_name="primary_fields.main",
                additional_input_instance=self.additional_input_instance,
                filler_column_index=None,
            )
            self.primary_widget.setAutoFillBackground(True)
            self.primary_widget.setObjectName("layout_primary_fields")
            self.primary_widget.setStyleSheet("QWidget#layout_primary_fields { border: none; }")
            input_layout.addWidget(self.primary_widget)

        # ── Subtabs (optional — only if schema has "tabs") ────────────────────────
        self.input_tabs = None

        if "tabs" in schema:
            self.input_tabs = QTabWidget()
            self.input_tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            self.input_tabs.setTabBarAutoHide(False)
            self.input_tabs.setStyleSheet("""
                QTabBar { background-color: #e8e8e8; border: 1px solid red; }
                QTabWidget::pane { border: none; background-color: #f5f5f5; }
                QTabBar::tab {
                    background-color: #e8e8e8; color: #555; padding: 10px 20px;
                    border: 1px solid #b0b0b0; border-bottom: none; border-right: none;
                    font-size: 11px; min-width: 80px;
                }
                QTabBar::tab:disabled { color: #bfbfbf; background: #e6e6e6; }
                QTabBar::tab:last { border-right: 1px solid #b0b0b0; }
                QTabBar::tab:selected {
                    background-color: #90AF13; color: white; font-weight: bold;
                    border: 1px solid #90AF13; border-bottom: none;
                }
                QTabBar::tab:hover:!selected { background-color: #d0d0d0; }
            """)
            self.input_tabs.tabBar().setElideMode(Qt.ElideNone)
            self.input_tabs.tabBar().setExpanding(False)
            self.input_tabs.tabBar().setUsesScrollButtons(True)
            self.input_tabs.tabBar().setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

            for tab_def in schema["tabs"]:
                tab_id = tab_def["id"]
                tab_widget = UIBuilder(
                    owner=self,
                    schema=tab_def,
                    card_title="Inputs:",
                    main_widget_object_name=tab_id + ".main",
                    additional_input_instance=self.additional_input_instance,
                    filler_column_index=2,
                )
                self._tab_widgets[tab_id] = tab_widget
                self.input_tabs.addTab(tab_widget, tab_def["label"])

            QTimer.singleShot(0, self._sync_subtab_bar_width)
            self.input_tabs.currentChanged.connect(self._on_subtab_changed)
            self._on_subtab_changed(self.input_tabs.currentIndex())
            input_layout.addWidget(self.input_tabs)

        # ── Scroll wrapper ────────────────────────────────────────────────────────
        self.lower_scroll = QScrollArea()
        self.lower_scroll.setWidgetResizable(True)
        self.lower_scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.lower_scroll.setFrameShape(QFrame.NoFrame)
        self.lower_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.lower_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.lower_scroll.setStyleSheet(ADDITIONAL_INPUTS_SCROLL_STYLE + """
            QScrollArea { border: 1px solid #b0b0b0; border-radius: 0px 0px 8px 8px; background: white; }
        """)
        self.lower_scroll.setWidget(input_container)
        main_layout.addWidget(self.lower_scroll)

        # ── Post-build wiring ─────────────────────────────────────────────────────
        self._initialize_lane_defaults()
        if self.deck_thickness:
            self.deck_thickness.textChanged.connect(self.update_footpath_thickness)
        self.recalculate_girders()

        crash_barrier_type = self._find_crash_barrier_widget(KEY_CB_TYPE)
        if crash_barrier_type:
            barrier_type = crash_barrier_type.currentText()
            self._update_crash_barrier_visibility(barrier_type)
            self._apply_crash_barrier_defaults(barrier_type, force=False)
        median_type_w = self._find_median_widget(KEY_MD_TYPE)
        if median_type_w:
            self._apply_median_defaults(median_type_w.currentText(), force=False)
        if self._find_railing_widget(KEY_RL_LOAD_MODE):
            self._apply_railing_defaults(force=False)
        wearing_material_w = self._find_wearing_widget(KEY_WC_MATERIAL)

        if wearing_material_w:
            self.on_wearing_material_changed(wearing_material_w.currentText())

        try:
            if self.no_of_girders and self.no_of_girders.text():
                self.girder_count_changed.emit(int(self.no_of_girders.text()))
        except Exception:
            pass

    def _sync_tab_active_states(self):
        """Enable/disable subtabs based on their 'active' condition in schema.
        
        Each tab_def may have an 'active' key:
            "active": {
                "id": KEY_FOOTPATH,       # key to check in working_input_dict
                "values": ["Both Sides", "Single Side"],  # enabled when value is in this list
            }
        Tabs without 'active' are always enabled.
        """
        d = self.additional_input_instance.working_input_dict
        for tab_def in TYPICAL_SECTION_SCHEMA["tabs"]:
            active_def = tab_def.get("active")
            if not active_def:
                continue
            tab_widget = self._tab_widgets.get(tab_def["id"])
            if not tab_widget:
                continue
            # Enable tab only if current dict value is in the allowed values list
            enabled = d.get(active_def["id"]) in active_def["values"]
            self.input_tabs.setTabEnabled(self.input_tabs.indexOf(tab_widget), enabled)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._sync_subtab_bar_width()

    def _on_subtab_changed(self, index):
        if not hasattr(self, "input_tabs") or self.input_tabs is None:
            return
        for i in range(self.input_tabs.count()):
            widget = self.input_tabs.widget(i)
            if i == index:
                widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            else:
                widget.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        # Notify the layout system that the size hint has changed
        self.input_tabs.updateGeometry()

    def _sync_subtab_bar_width(self):
        # Removed the forced fixed width constraint so the scroll buttons 
        # can actually appear when the tabs overflow the widget area.
        pass


    # ----- Layout / Deck Details sub-tab ---------------------------------------

    def _get_footpath_count(self):
        if self._initial_cad_state.get("footpath_config") == "both":
            return 2
        if self._initial_cad_state.get("footpath_config") == "left":
            return 1
        return 0

    def _get_flange_width_limit(self):
        # Widths are defined elsewhere (Girder Details) in mm; if unavailable, assume 0
        top_width_mm = getattr(self, "top_flange_width_mm", 0) or 0
        bottom_width_mm = getattr(self, "bottom_flange_width_mm", 0) or 0
        return max(top_width_mm, bottom_width_mm) / 1000.0

    def _parse_length_value(self, field, default=0.0, scale=1.0):
        try:
            text = field.text().strip() if field else ""
            if text:
                return float(text) / scale
        except (ValueError, AttributeError):
            pass
        return default

    # --------------------- Lane Details sub-tab functionality  START ---------------------

    _LANE_WIDTH_M = 3.5  # IRC 5 Clause 104.3.1 minimum design lane width

    def _calculate_overall_bridge_width(self):
        carriageway_width = float(self.carriageway_width) if self.carriageway_width else 0.0
        crash_barrier_width = self._parse_length_value(
            self._find_crash_barrier_widget(KEY_CB_WIDTH),
            default=DEFAULT_CRASH_BARRIER_WIDTH,
        )
        footpath_width = self._parse_length_value(
            getattr(self, "footpath_width", None),
            default=0.0,
        )
        railing_width = self._parse_length_value(
            self._find_railing_widget(KEY_RL_WIDTH),
            default=DEFAULT_RAILING_WIDTH,
            scale=1000.0,
        )
        median_width = self._parse_length_value(
            self._find_median_widget(KEY_MD_WIDTH),
            default=0.0,
        )
        footpath_count = self._get_footpath_count()

        layout = CrossSectionLayout(
            carriageway_width=carriageway_width,
            crash_barrier_width=crash_barrier_width,
            railing_width=railing_width,
            footpath_width=footpath_width,
            median_width=median_width,
            no_of_footpaths=footpath_count,
        )
        return layout.total_width

    def _clear_adjust_notice(self):
        if hasattr(self, "layout_adjust_notice"):
            self.layout_adjust_notice.hide()
            self.layout_adjust_notice.setText("")
        if hasattr(self, "layout_warning_notice"):
            self.layout_warning_notice.hide()
            self.layout_warning_notice.setText("")
        if hasattr(self, "layout_notice_container"):
            self.layout_notice_container.hide()

    def _clear_layout_entry_fields(self, message: str) -> None:
        """Clear layout inputs together when any of them is emptied and show an error."""
        if self.updating_fields:
            return
        self.updating_fields = True
        try:
            for field in (
                getattr(self, "girder_spacing", None),
                getattr(self, "deck_overhang", None),
                getattr(self, "no_of_girders", None),
            ):
                if field is not None:
                    field.clear()
            # Reset tracked values
            self._last_spacing_value = None
            self._last_overhang_value = None
            self._last_girders_value = None
        finally:
            self.updating_fields = False
        self._clear_adjust_notice()
        CustomMessageBox(
            title="Layout",
            text=message,
            buttons=["OK"],
            dialogType=MessageBoxType.Warning,
        ).exec()

    def _show_adjust_notice(self, reason, warning=None):
        any_visible = bool(reason) or bool(warning)
        if hasattr(self, "layout_adjust_notice"):
            if reason and not warning:
                self.layout_adjust_notice.setText(f"Values adjusted: {reason}")
                self.layout_adjust_notice.show()
            else:
                self.layout_adjust_notice.hide()
                self.layout_adjust_notice.setText("")
        if hasattr(self, "layout_warning_notice"):
            if warning:
                self.layout_warning_notice.setText(f"Warning: {warning}")
                self.layout_warning_notice.show()
            else:
                self.layout_warning_notice.hide()
                self.layout_warning_notice.setText("")
        if hasattr(self, "layout_notice_container"):
            if any_visible:
                self.layout_notice_container.show()
            else:
                self.layout_notice_container.hide()

    def _set_layout_fields(self, spacing, overhang, girders):
        self.updating_fields = True
        try:
            self.girder_spacing.setText(f"{spacing:.2f}")
            self.deck_overhang.setText(f"{overhang:.2f}")
            self.no_of_girders.setText(str(int(girders)))
            # Update tracked values to prevent spurious recalculations
            self._last_spacing_value = spacing
            self._last_overhang_value = overhang
            self._last_girders_value = int(girders)
            try:
                self.girder_count_changed.emit(int(girders))
            except Exception:
                pass
        finally:
            self.updating_fields = False

    def _spacing_candidates_for_overhang(self, overall_width, overhang, spacing_bounds):
        """Find best (n, spacing) combination for a FIXED overhang.
        
        When user changes overhang, we keep overhang fixed and only adjust
        girder spacing and number of girders.
        
        Formula: overall_width = 2 * overhang + (n - 1) * spacing
        => spacing = (overall_width - 2 * overhang) / (n - 1)  for n >= 2
        """
        spacing_min, spacing_max = spacing_bounds
        max_n = int(math.floor(overall_width / spacing_min) + 2) if spacing_min > 0 else 50
        
        best = None
        for n in range(2, max(2, max_n) + 1):
            # For n >= 2: spacing = (overall_width - 2 * overhang) / (n - 1)
            raw_spacing = (overall_width - 2.0 * overhang) / (n - 1)
            if raw_spacing <= 0:
                continue
            
            # Round spacing to 2 decimal places for display
            s_rounded = round(raw_spacing, 2)
            
            # Check if rounded spacing is within valid bounds
            if s_rounded < spacing_min - 1e-6 or s_rounded > spacing_max + 1e-6:
                continue
            
            s_rounded = max(spacing_min, min(spacing_max, s_rounded))
            
            # Prefer n values that result in overhang being 0.35-0.5 of spacing (ideal range)
            ideal_min = 0.35 * s_rounded
            ideal_max = 0.5 * s_rounded
            if ideal_min <= overhang <= ideal_max:
                score = (0, n)  # Ideal range, prefer lower n
            else:
                # Not in ideal range but still valid
                score = (1, n)
            
            if best is None or score < best[0]:
                best = (score, s_rounded, overhang, n)
        
        return best

    def _pick_n_for_spacing(self, overall_width, spacing, spacing_bounds):
        """Find best (n, overhang) combination for a FIXED spacing.
        
        When user changes spacing, we keep spacing fixed and only adjust
        number of girders and overhang.
        
        Formula: overall_width = 2 * overhang + (n - 1) * spacing
        => overhang = (overall_width - (n - 1) * spacing) / 2
        
        Ideally overhang should be 0.35 to 0.5 of spacing. If not possible,
        allow overhang to vary between 0 and overall_width/2.
        """
        spacing_min, spacing_max = spacing_bounds
        spacing = max(spacing_min, min(spacing_max, round(spacing, 2)))
        
        o_min, o_max = (0.0, 0.0) if overall_width <= 0 else (0.0, overall_width / 2.0)
        max_n = int(math.floor(overall_width / spacing) + 2) if spacing > 0 else 1
        
        # Ideal overhang range: 0.35 to 0.5 of spacing
        ideal_overhang_min = 0.35 * spacing
        ideal_overhang_max = 0.5 * spacing
        
        best = None
        for n in range(2, max(2, max_n) + 1):
            if (n - 1) * spacing > overall_width + 1e-6:
                break
            
            overhang = (overall_width - (n - 1) * spacing) / 2.0
            
            # Check if overhang is within valid range (0 to overall_width/2)
            if overhang < o_min - 1e-6 or overhang > o_max + 1e-6:
                continue
            
            # Score: prefer overhang in ideal range (0.35-0.5 of spacing)
            if ideal_overhang_min <= overhang <= ideal_overhang_max:
                # In ideal range
                score = (0, abs(overhang - (ideal_overhang_min + ideal_overhang_max) / 2), n)
            elif overhang <= spacing:
                # Not in ideal range but overhang <= spacing (acceptable)
                score = (1, abs(overhang - ideal_overhang_max), n)
            else:
                # Overhang > spacing (less desirable but valid)
                score = (2, overhang - spacing, n)
            
            if best is None or score < best[0]:
                best = (score, n, spacing, overhang)
        
        return best

    def _solve_layout(self, changed_field="width"):
        if self.updating_fields:
            return
        self._clear_adjust_notice()
        overall_width = self.get_overall_bridge_width()
        if overall_width <= 0:
            CustomMessageBox(
                title="Layout",
                text="Overall bridge width must be positive.",
                buttons=["OK"],
                dialogType=MessageBoxType.Warning,
            ).exec()
            return

        _flange_lim = (max(getattr(self,"top_flange_width_mm",0) or 0, getattr(self,"bottom_flange_width_mm",0) or 0)) / 1000.0
        spacing_bounds = (1.0, max(1.0, overall_width - _flange_lim))
        spacing_input = self._parse_length_value(self.girder_spacing, default=DEFAULT_GIRDER_SPACING)
        overhang_input = self._parse_length_value(self.deck_overhang, default=0.35 * spacing_input)
        girders_input = None
        if self.no_of_girders.text().strip():
            try:
                girders_input = int(self.no_of_girders.text().strip())
            except ValueError:
                girders_input = None

        o_min, o_max = (0.0, 0.0) if overall_width <= 0 else (0.0, overall_width / 2.0)

        if changed_field == "spacing":
            pick = self._pick_n_for_spacing(overall_width, spacing_input, spacing_bounds)
            if not pick:
                CustomMessageBox(
                    title="Layout",
                    text="Cannot satisfy constraints with the selected girder spacing.",
                    buttons=["OK"],
                    dialogType=MessageBoxType.Warning,
                ).exec()
                self._update_overall_bridge_width_display()
                return
            _, n, spacing_use, overhang_use = pick
            # Capture old values BEFORE setting new ones
            old_girders = girders_input
            old_overhang = overhang_input
            old_spacing = spacing_input
            self._set_layout_fields(spacing_use, overhang_use, n)
            reason_parts = []
            # Spacing should be kept as user specified (only minor rounding allowed)
            if abs(spacing_use - old_spacing) > 0.01:
                reason_parts.append(f"spacing {old_spacing:.2f}→{spacing_use:.2f}")
            if abs(overhang_use - old_overhang) > 1e-6:
                reason_parts.append(f"overhang {old_overhang:.2f}→{overhang_use:.2f}")
            if old_girders is not None and n != old_girders:
                reason_parts.append(f"girders {old_girders}→{n}")
            
            # Check if overhang exceeds girder spacing and show warning
            warning_msg = None
            if overhang_use > spacing_use + 1e-6:
                warning_msg = f"Overhang ({overhang_use:.2f} m) exceeds girder spacing ({spacing_use:.2f} m)"
            
            if reason_parts:
                self._show_adjust_notice(", ".join(reason_parts), warning_msg)
            elif warning_msg:
                self._show_adjust_notice(None, warning_msg)
            self._update_overall_bridge_width_display()
            return

        if changed_field == "overhang":
            # Check if user entered a value exceeding the maximum possible overhang
            if overhang_input < o_min - 1e-6 or overhang_input > o_max + 1e-6:
                CustomMessageBox(
                    title="Deck Overhang Width Error",
                    text=f"Deck overhang width must be between {o_min:.2f} m and {o_max:.2f} m "
                        f"(half of Overall Bridge Width).\n\n"
                        f"Valid range: {o_min:.2f} m to {o_max:.2f} m\n"
                        f"You entered: {overhang_input:.2f} m\n\n"
                        "To change deck overhang limits, you need to adjust the Overall Bridge Width "
                        "(by modifying carriageway width, crash barriers, footpaths, etc.).",
                    buttons=["OK"],
                    dialogType=MessageBoxType.Warning,
                ).exec()
                self._update_overall_bridge_width_display()
                return
            
            # Keep overhang fixed as user specified
            overhang_use = overhang_input
            pick = self._spacing_candidates_for_overhang(overall_width, overhang_use, spacing_bounds)
            if not pick:
                CustomMessageBox(
                    title="Layout",
                    text="Cannot satisfy constraints with the selected deck overhang.",
                    buttons=["OK"],
                    dialogType=MessageBoxType.Warning,
                ).exec()
                self._update_overall_bridge_width_display()
                return
            _, spacing_use, _, n = pick
            # Capture old values for comparison
            old_overhang = overhang_input
            old_spacing = spacing_input
            old_girders = girders_input
            self._set_layout_fields(spacing_use, overhang_use, n)
            reason_parts = []
            # Overhang should not change since user specified it
            if abs(spacing_use - old_spacing) > 1e-6:
                reason_parts.append(f"spacing {old_spacing:.2f}→{spacing_use:.2f}")
            if old_girders is not None and n != old_girders:
                reason_parts.append(f"girders {old_girders}→{n}")
            
            # Check if overhang exceeds girder spacing and show warning
            warning_msg = None
            if overhang_use > spacing_use + 1e-6:
                warning_msg = f"Overhang ({overhang_use:.2f} m) exceeds girder spacing ({spacing_use:.2f} m)"
            
            if reason_parts:
                self._show_adjust_notice(", ".join(reason_parts), warning_msg)
            elif warning_msg:
                self._show_adjust_notice(None, warning_msg)
            self._update_overall_bridge_width_display()
            return

        if changed_field == "girders":
            if girders_input is None or girders_input < 2:
                CustomMessageBox(
                    title="Layout",
                    text="Number of girders must be an integer greater than or equal to 2.",
                    buttons=["OK"],
                    dialogType=MessageBoxType.Warning,
                ).exec()
                if girders_input is None:
                    return
                girders_input = 2
                self._set_layout_fields(spacing_input, overhang_input, girders_input)
            n = girders_input
            # Capture old values for comparison
            old_overhang = overhang_input
            old_spacing = spacing_input

            # If the selected number of girders cannot fit within the current
            # overall bridge width, clamp to the maximum feasible count.
            # With minimum spacing and non-negative overhang:
            # overall_width >= (n-1) * spacing_min  =>  n_max = floor(overall_width/spacing_min) + 1
            try:
                spacing_min = float(spacing_bounds[0])
            except Exception:
                spacing_min = 1.0
            if spacing_min <= 0:
                spacing_min = 1.0
            n_max = int(math.floor((overall_width + 1e-9) / spacing_min) + 1)
            n_max = max(2, n_max)
            if n > n_max:
                # Clamp and proceed with a valid solution rather than leaving
                # the UI with an impossible n value.
                n = n_max

            # For n >= 2: overall_width = 2*overhang + (n-1)*spacing
            # Keep n fixed, try to find spacing and overhang such that overhang is in ideal range
            # Ideal overhang = 0.35 to 0.5 of spacing
            
            # Try to keep overhang in ideal range (0.35-0.5 of spacing)
            # From formula: spacing = (overall_width - 2*overhang) / (n-1)
            # If overhang = 0.35*spacing => spacing = overall_width / (n-1 + 0.7)
            # If overhang = 0.5*spacing => spacing = overall_width / (n-1 + 1.0) = overall_width / n
            
            # Try target spacing that gives overhang in ideal range
            ideal_spacing_for_0_35 = overall_width / (n - 1 + 0.7)
            ideal_spacing_for_0_50 = overall_width / n
            
            # Pick spacing that's in the middle of the ideal range
            target_spacing = (ideal_spacing_for_0_35 + ideal_spacing_for_0_50) / 2.0
            spacing_use = max(spacing_bounds[0], min(spacing_bounds[1], round(target_spacing, 2)))
            overhang_use = (overall_width - (n - 1) * spacing_use) / 2.0
            
            # Check if overhang is within valid range
            if overhang_use < o_min - 1e-6 or overhang_use > o_max + 1e-6:
                CustomMessageBox(
                    title="Layout",
                    text="Cannot satisfy constraints with the selected number of girders. "
                    f"For the current overall width ({overall_width:.2f} m) and minimum spacing ({spacing_min:.2f} m), "
                    f"maximum feasible girders is {n_max}.",
                    buttons=["OK"],
                    dialogType=MessageBoxType.Warning,
                )
                # Revert to a safe fallback (previous value if available, else 2)
                fallback_n = int(getattr(self, "_last_girders_value", 2) or 2)
                fallback_n = max(2, min(fallback_n, n_max))
                pick = self._pick_n_for_spacing(overall_width, spacing_use, spacing_bounds)
                if pick:
                    _, fallback_n2, spacing_f, overhang_f = pick
                    fallback_n = max(2, min(int(fallback_n2), n_max))
                    self._set_layout_fields(spacing_f, overhang_f, fallback_n)
                else:
                    self._set_layout_fields(max(spacing_bounds[0], min(spacing_bounds[1], spacing_use)), max(o_min, min(o_max, max(0.0, overhang_use))), fallback_n)
                self._update_overall_bridge_width_display()
                return
            
            self._set_layout_fields(spacing_use, overhang_use, n)
            reason_parts = []
            if abs(spacing_use - old_spacing) > 0.01:
                reason_parts.append(f"spacing {old_spacing:.2f}→{spacing_use:.2f}")
            if abs(overhang_use - old_overhang) > 1e-6:
                reason_parts.append(f"overhang {old_overhang:.2f}→{overhang_use:.2f}")
            if girders_input is not None and n != girders_input:
                reason_parts.append(f"girders {girders_input}→{n}")
            
            # Check if overhang exceeds girder spacing and show warning
            warning_msg = None
            if overhang_use > spacing_use + 1e-6:
                warning_msg = f"Overhang ({overhang_use:.2f} m) exceeds girder spacing ({spacing_use:.2f} m)"
            
            if reason_parts:
                self._show_adjust_notice(", ".join(reason_parts), warning_msg)
            elif warning_msg:
                self._show_adjust_notice(None, warning_msg)
            self._update_overall_bridge_width_display()
            return

        # Default / overall width change: try to keep current spacing if feasible
        # Capture old values for comparison
        old_spacing = spacing_input
        old_overhang = overhang_input
        old_girders = girders_input
        pick = self._pick_n_for_spacing(overall_width, old_spacing, spacing_bounds)
        if not pick:
            # Fallback to default spacing
            pick = self._pick_n_for_spacing(overall_width, DEFAULT_GIRDER_SPACING, spacing_bounds)
        if pick:
            _, n, spacing_use, overhang_use = pick
            self._set_layout_fields(spacing_use, overhang_use, n)
            reason_parts = []
            if abs(spacing_use - old_spacing) > 0.01:
                reason_parts.append(f"spacing {old_spacing:.2f}→{spacing_use:.2f}")
            if abs(overhang_use - old_overhang) > 1e-6:
                reason_parts.append(f"overhang {old_overhang:.2f}→{overhang_use:.2f}")
            if old_girders is not None and n != old_girders:
                reason_parts.append(f"girders {old_girders}→{n}")
            
            # Check if overhang exceeds girder spacing and show warning
            warning_msg = None
            if overhang_use > spacing_use + 1e-6:
                warning_msg = f"Overhang ({overhang_use:.2f} m) exceeds girder spacing ({spacing_use:.2f} m)"
            
            if reason_parts:
                self._show_adjust_notice(", ".join(reason_parts), warning_msg)
            elif warning_msg:
                self._show_adjust_notice(None, warning_msg)
        else:
            CustomMessageBox(
                title="Layout",
                text="Cannot satisfy layout constraints for the current overall width.",
                buttons=["OK"],
                dialogType=MessageBoxType.Warning,
            ).exec()
        self._update_overall_bridge_width_display()

    def get_overall_bridge_width(self):
        try:
            return self._calculate_overall_bridge_width()
        except:
            return self.carriageway_width

    def _update_overall_bridge_width_display(self):
        if hasattr(self, "overall_bridge_width_display"):
            try:
                overall_width = self.get_overall_bridge_width()
                self._updating_overall_width_display = True
                self.overall_bridge_width_display.setText(f"{overall_width:.2f}")
                self._updating_overall_width_display = False
            except:
                self._updating_overall_width_display = False
                self.overall_bridge_width_display.clear()

    def _reject_overall_width_override(self, text):
        if self._updating_overall_width_display:
            return
        try:
            entered_value = float(text) if text else None
        except ValueError:
            entered_value = None

        expected_value = self._calculate_overall_bridge_width()
        if entered_value is None or abs(expected_value - entered_value) > 1e-6:
            if self.overall_bridge_width_display.hasFocus():
                CustomMessageBox(
                    title="Overall Bridge Width Locked",
                    text="Overall Bridge Width is auto-calculated using:\n"
                         f"{self.overall_bridge_width_formula}",
                    buttons=["OK"],
                    dialogType=MessageBoxType.Warning,
                ).exec()
            self._update_overall_bridge_width_display()

    def recalculate_girders(self):
        self._update_overall_bridge_width_display()
        self._solve_layout("width")

    def on_girder_spacing_changed(self):
        if self.updating_fields:
            return
        if not self.girder_spacing.text().strip():
            self._clear_layout_entry_fields("Girder spacing, deck overhang, and number of girders are linked. Please enter all three.")
            self._last_spacing_value = None
            return
        try:
            new_val = float(self.girder_spacing.text().strip())
        except ValueError:
            return
        # Skip recalculation if numeric value unchanged (e.g., "2.50" -> "2.5")
        if self._last_spacing_value is not None and abs(new_val - self._last_spacing_value) < 1e-6:
            return
        self._last_spacing_value = new_val
        self._solve_layout("spacing")

    def on_deck_overhang_changed(self):
        if self.updating_fields:
            return
        if not self.deck_overhang.text().strip():
            self._clear_layout_entry_fields("Girder spacing, deck overhang, and number of girders are linked. Please enter all three.")
            self._last_overhang_value = None
            return
        try:
            new_val = float(self.deck_overhang.text().strip())
        except ValueError:
            return
        # Skip recalculation if numeric value unchanged (e.g., "1.31" -> "1.310")
        if self._last_overhang_value is not None and abs(new_val - self._last_overhang_value) < 1e-6:
            return
        self._last_overhang_value = new_val
        self._solve_layout("overhang")

    def on_no_of_girders_changed(self):
        if self.updating_fields:
            return
        if not self.no_of_girders.text().strip():
            self._clear_layout_entry_fields("Girder spacing, deck overhang, and number of girders are linked. Please enter all three.")
            self._last_girders_value = None
            return
        try:
            new_val = int(float(self.no_of_girders.text().strip()))
        except ValueError:
            return
        # Skip recalculation if numeric value unchanged (e.g., "2.00" -> "2")
        if self._last_girders_value is not None and new_val == self._last_girders_value:
            return
        self._last_girders_value = new_val
        self._solve_layout("girders")

    def on_footpath_width_changed(self):
        if not self.updating_fields:
            self.recalculate_girders()

    def update_footpath_value(self, footpath_value):
        fp_map = {"Both Sides": "both", "Single Side": "left", "None": "none"}
        self._initial_cad_state = dict(getattr(self, "_initial_cad_state", None) or {})
        self._initial_cad_state["footpath_config"] = fp_map.get(footpath_value, "none")
        if hasattr(self, "footpath_width"):
            self.footpath_width.setEnabled(footpath_value != "None")
        if hasattr(self, "footpath_thickness"):
            self.footpath_thickness.setEnabled(footpath_value != "None")
        self.recalculate_girders()

    def validate_footpath_width(self):
        try:
            if self.footpath_width.text():
                width = float(self.footpath_width.text())
                if width < MIN_FOOTPATH_WIDTH:
                    CustomMessageBox(
                        title="Footpath Width Error",
                        text=f"Footpath width must be at least {MIN_FOOTPATH_WIDTH} m as per IRC 5 Clause 104.3.6.",
                        buttons=["OK"],
                        dialogType=MessageBoxType.Critical,
                    ).exec()
        except:
            pass

    def _validate_thickness_field(self, field, min_val, max_val, default_val, too_small_msg, too_large_msg):
        try:
            text = field.text().strip()
            if not text:
                field.setText(str(int(default_val)))
                return
            value = float(text)
            if value < min_val:
                CustomMessageBox(
                    title="Thickness Error",
                    text=too_small_msg,
                    buttons=["OK"],
                    dialogType=MessageBoxType.Critical,
                ).exec()
                field.setText(str(int(min_val)))
            elif value > max_val:
                CustomMessageBox(
                    title="Thickness Error",
                    text=too_large_msg,
                    buttons=["OK"],
                    dialogType=MessageBoxType.Critical,
                ).exec()
                field.setText(str(int(max_val)))
        except:
            field.setText(str(int(default_val)))

    def _validate_thickness_helper(self, field, label):
        """Validate deck/footpath thickness: must be 100–500 mm."""
        self._validate_thickness_field(field, 100, 500, 200,
            f"{label} thickness too small", f"{label} thickness too large")

    def validate_deck_thickness(self):
        self._validate_thickness_helper(self.deck_thickness, "Deck")

    def validate_footpath_thickness(self):
        self._validate_thickness_helper(self.footpath_thickness, "Footpath")

    def update_footpath_thickness(self):
        if self.deck_thickness.text() and not self.footpath_thickness.text():
            self.footpath_thickness.setText(self.deck_thickness.text())


    # ----- Crash Barrier sub-tab -----------------------------------------------

    def _is_rcc_barrier(self, barrier_type):
        return (
            barrier_type.startswith("IRC 5 - RCC Crash Barrier")
            or barrier_type.startswith("IRC 5 - High Containment RCC Crash Barrier")
        )

    def _is_metallic_barrier(self, barrier_type):
        return barrier_type.startswith("IRC 5 - Metallic Crash Barrier")

    def _effective_crash_barrier_type(self, barrier_type):
        return "IRC 5 - RCC Crash Barrier" if barrier_type == "Custom" else barrier_type

    def _update_crash_barrier_visibility(self, barrier_type):
        is_metallic = self._is_metallic_barrier(barrier_type)
        is_rcc = self._is_rcc_barrier(barrier_type)
        is_custom = barrier_type == "Custom"
        crash_barrier_density = self._find_crash_barrier_widget(KEY_CB_DENSITY)
        crash_barrier_density_label = self._find_crash_barrier_widget(f"{KEY_CB_DENSITY}_label")
        crash_barrier_area = self._find_crash_barrier_widget(KEY_CB_AREA)
        crash_barrier_area_label = self._find_crash_barrier_widget(f"{KEY_CB_AREA}_label")
        crash_barrier_post_spacing = self._find_crash_barrier_widget(KEY_CB_POST_SPACING)
        crash_barrier_post_spacing_label = self._find_crash_barrier_widget(f"{KEY_CB_POST_SPACING}_label")
        crash_barrier_load = self._find_crash_barrier_widget(KEY_CB_LOAD)
        crash_barrier_width = self._find_crash_barrier_widget(KEY_CB_WIDTH)
        crash_barrier_height = self._find_crash_barrier_widget(KEY_CB_HEIGHT)

        # Density & Area hidden for metallic or custom options
        hide_density_area = is_metallic or is_custom
        for widget in [crash_barrier_density, crash_barrier_density_label, crash_barrier_area, crash_barrier_area_label]:
            if widget:
                widget.setVisible(not hide_density_area)
        if hide_density_area:
            if crash_barrier_density:
                crash_barrier_density.clear()
            if crash_barrier_area:
                crash_barrier_area.clear()

        # Post spacing only for metallic
        for widget in [crash_barrier_post_spacing, crash_barrier_post_spacing_label]:
            if widget:
                widget.setVisible(is_metallic)
        if is_metallic and crash_barrier_post_spacing and not crash_barrier_post_spacing.text():
            crash_barrier_post_spacing.setText("1")
        if not is_metallic:
            if crash_barrier_post_spacing:
                crash_barrier_post_spacing.clear()

        # Load behavior
        if crash_barrier_load:
            crash_barrier_load.setEnabled(is_custom)
            crash_barrier_load.setReadOnly(is_rcc)
            crash_barrier_load.setPlaceholderText("" if not is_custom else "Enter custom load per IRC 6 guidance")
        if is_rcc:
            self._auto_compute_crash_barrier_load()
        else:
            if crash_barrier_load:
                crash_barrier_load.setReadOnly(False)

        # Grey out fixed parameters per IRC 5
        for widget in [crash_barrier_density, crash_barrier_width, crash_barrier_height, crash_barrier_area]:
            if widget:
                widget.setEnabled(is_custom)

    def _auto_compute_crash_barrier_load(self):
        crash_barrier_type = self._find_crash_barrier_widget(KEY_CB_TYPE)
        crash_barrier_density = self._find_crash_barrier_widget(KEY_CB_DENSITY)
        crash_barrier_area = self._find_crash_barrier_widget(KEY_CB_AREA)
        crash_barrier_load = self._find_crash_barrier_widget(KEY_CB_LOAD)
        barrier_type = crash_barrier_type.currentText() if crash_barrier_type else ""
        if self._is_rcc_barrier(barrier_type):
            try:
                density = float(crash_barrier_density.text()) if crash_barrier_density and crash_barrier_density.text() else 0.0
                area = float(crash_barrier_area.text()) if crash_barrier_area and crash_barrier_area.text() else 0.0
                load = density * area
                if crash_barrier_load:
                    crash_barrier_load.setText(f"{load:.2f}")
            except:
                if crash_barrier_load:
                    crash_barrier_load.clear()
        # For other types load is user-entered; do not overwrite

    def _apply_crash_barrier_defaults(self, barrier_type: str, force: bool = False):
        """Populate recommended defaults per IRC 5 selections.
        force=True overwrites existing values (used on reset). Otherwise, only fill missing fields.
        """
        crash_barrier_density = self._find_crash_barrier_widget(KEY_CB_DENSITY)
        crash_barrier_width = self._find_crash_barrier_widget(KEY_CB_WIDTH)
        crash_barrier_height = self._find_crash_barrier_widget(KEY_CB_HEIGHT)
        crash_barrier_area = self._find_crash_barrier_widget(KEY_CB_AREA)
        crash_barrier_load = self._find_crash_barrier_widget(KEY_CB_LOAD)
        crash_barrier_post_spacing = self._find_crash_barrier_widget(KEY_CB_POST_SPACING)
        if not crash_barrier_density:
            return

        is_rcc = self._is_rcc_barrier(barrier_type)
        is_metallic = self._is_metallic_barrier(barrier_type)
        is_custom = barrier_type == "Custom"

        effective_barrier_type = self._effective_crash_barrier_type(barrier_type)
        geom = CrashBarrierGeometry.get_geometry(effective_barrier_type)
     

        def _set(widget, value: str):
            if widget is None:
                return
            if force or not widget.text():
                widget.setText(value)

        if is_rcc and geom:
            _set(crash_barrier_density, f"{DEFAULT_CONCRETE_DENSITY:.1f}")

            if "bottom_width" in geom:
                _set(crash_barrier_width, f"{geom['bottom_width'] / 1000:.2f}")


            if "total_height" in geom:
                _set(crash_barrier_height, f"{geom['total_height'] / 1000:.2f}")
            if crash_barrier_width and crash_barrier_height:
                try:
                    w_val = float(crash_barrier_width.text() or 0.0)
                    h_val = float(crash_barrier_height.text() or 0.0)
                    area_val = w_val * h_val
                    _set(crash_barrier_area, f"{area_val:.2f}")
                except:
                    pass
            self._auto_compute_crash_barrier_load()
        elif is_metallic:
            if crash_barrier_post_spacing:
                _set(crash_barrier_post_spacing, "1")
            if force and crash_barrier_load:
                crash_barrier_load.clear()
        elif is_custom:
            if geom:
                if "bottom_width" in geom:
                    _set(crash_barrier_width, f"{geom['bottom_width'] / 1000:.2f}")
                if "total_height" in geom:
                    _set(crash_barrier_height, f"{geom['total_height'] / 1000:.2f}")
            if force and crash_barrier_load:
                crash_barrier_load.clear()

        self._update_crash_barrier_visibility(barrier_type)
        # ----  CAD UPDATE AFTER DEFAULTS CHANGE ----
        if hasattr(self, "cad_preview"):
            params = {
                KEY_CB_TYPE: barrier_type,
            }

            if crash_barrier_width and crash_barrier_width.text():
                params[KEY_CB_WIDTH] = float(crash_barrier_width.text()) * 1000

            if crash_barrier_height and crash_barrier_height.text():
                params[KEY_CB_HEIGHT] = float(crash_barrier_height.text()) * 1000

            self.cad_preview.update_params(params)

    def _reset_crash_barrier_defaults(self):
        crash_barrier_type = self._find_crash_barrier_widget(KEY_CB_TYPE)
        crash_barrier_post_spacing = self._find_crash_barrier_widget(KEY_CB_POST_SPACING)
        if crash_barrier_type:
            crash_barrier_type.setCurrentText("IRC 5 - RCC Crash Barrier")
        if crash_barrier_post_spacing:
            crash_barrier_post_spacing.setText("1")
        if crash_barrier_type:
            barrier_type = crash_barrier_type.currentText()
            self._update_crash_barrier_visibility(barrier_type)
            self._apply_crash_barrier_defaults(barrier_type, force=True)

    def on_crash_barrier_type_changed(self, barrier_type):
        # IMPORTANT: force=True so layout recalculation cannot override geometry
        self._update_crash_barrier_visibility(barrier_type)
        self._apply_crash_barrier_defaults(barrier_type, force=True)

        # Recalculate AFTER geometry is locked
        self.recalculate_girders()

    # ----- Median sub-tab ------------------------------------------------------

    def _is_rcc_median(self, median_type):
        return median_type.startswith("IRC 5 - RCC Crash Barrier") or median_type.startswith("IRC 5 - Raised Kerb")

    def _is_metallic_median(self, median_type):
        return median_type.startswith("IRC 5 - Metallic Crash Barrier")

    def _effective_median_type(self, median_type):
        return "IRC 5 - Raised Kerb" if median_type == "Custom" else median_type

    def _auto_compute_median_load(self):
        median_type_w = self._find_median_widget(KEY_MD_TYPE)
        median_type = median_type_w.currentText() if median_type_w else ""
        median_density = self._find_median_widget(KEY_MD_DENSITY)
        median_area = self._find_median_widget(KEY_MD_AREA)
        median_load = self._find_median_widget(KEY_MD_LOAD)
        if self._is_rcc_median(median_type):
            try:
                density = float(median_density.text()) if median_density and median_density.text() else 0.0
                area = float(median_area.text()) if median_area and median_area.text() else 0.0
                load = density * area
                if median_load:
                    median_load.setText(f"{load:.2f}")
            except:
                if median_load:
                    median_load.clear()

    def _update_median_visibility(self, median_type, include_median=True):
        is_metallic = self._is_metallic_median(median_type)
        is_rcc = self._is_rcc_median(median_type)
        is_custom = median_type == "Custom"
        active = bool(include_median)

        median_type_w = self._find_median_widget(KEY_MD_TYPE)
        median_density = self._find_median_widget(KEY_MD_DENSITY)
        median_width = self._find_median_widget(KEY_MD_WIDTH)
        median_height = self._find_median_widget(KEY_MD_HEIGHT)
        median_area = self._find_median_widget(KEY_MD_AREA)
        median_load = self._find_median_widget(KEY_MD_LOAD)
        median_post_spacing = self._find_median_widget(KEY_MD_POST_SPACING)
        median_density_label = self._find_median_widget(f"{KEY_MD_DENSITY}_label")
        median_area_label = self._find_median_widget(f"{KEY_MD_AREA}_label")
        median_post_spacing_label = self._find_median_widget(f"{KEY_MD_POST_SPACING}_label")

        # Gray-out: disable entire card when not included
        for widget in [
            median_type_w,
            median_density,
            median_width,
            median_height,
            median_area,
            median_load,
            median_post_spacing,
            median_density_label,
            median_area_label,
            median_post_spacing_label,
        ]:
            if widget is not None:
                widget.setEnabled(active)

        # Density & Area hidden for metallic or custom
        hide_density_area = is_metallic or is_custom
        for widget in [median_density, median_density_label, median_area, median_area_label]:
            if widget is not None:
                widget.setVisible(active and not hide_density_area)
        if hide_density_area:
            if median_density:
                median_density.clear()
            if median_area:
                median_area.clear()

        # Post spacing only for metallic
        for widget in [median_post_spacing, median_post_spacing_label]:
            if widget is not None:
                widget.setVisible(active and is_metallic)
        if active and is_metallic and median_post_spacing and not median_post_spacing.text():
            median_post_spacing.setText("1")
        if active and not is_metallic and median_post_spacing:
            median_post_spacing.clear()

        # Load behavior
        if median_load:
            median_load.setEnabled(active)
            median_load.setReadOnly(active and is_rcc)
            if active:
                median_load.setPlaceholderText("" if not is_custom else "Enter custom load per IRC 6 guidance")
        if active and is_rcc:
            self._auto_compute_median_load()
        elif active and median_load:
            median_load.setReadOnly(False)
            median_load.clear()

        # Grey out fixed parameters per IRC 5
        if active:
            # RCC: density, width, height, area, load all fixed
            # Metallic: density(hidden), width, height, area(hidden), load fixed - only spacing editable
            # Custom: everything editable
            for widget in [median_density, median_width, median_height, median_area, median_load]:
                if widget:
                    widget.setEnabled(is_custom)
            if median_post_spacing:
                median_post_spacing.setEnabled(is_custom or is_metallic)

    def _apply_median_defaults(self, median_type: str, force: bool = False):
        median_density = self._find_median_widget(KEY_MD_DENSITY)
        if not median_density:
            return

        median_width = self._find_median_widget(KEY_MD_WIDTH)
        median_height = self._find_median_widget(KEY_MD_HEIGHT)
        median_area = self._find_median_widget(KEY_MD_AREA)
        median_load = self._find_median_widget(KEY_MD_LOAD)
        median_post_spacing = self._find_median_widget(KEY_MD_POST_SPACING)

        is_rcc = self._is_rcc_median(median_type)
        is_metallic = self._is_metallic_median(median_type)
        is_custom = median_type == "Custom"

        effective_median_type = self._effective_median_type(median_type)
        geom = MedianGeometry.get_geometry(effective_median_type)

        def _set(widget, value: str):
            if widget is None:
                return
            if force or not widget.text():
                widget.setText(value)

        if is_rcc and geom:
            _set(median_density, f"{DEFAULT_CONCRETE_DENSITY:.1f}")

            if KEY_MD_WIDTH in geom:
                _set(median_width, f"{geom[KEY_MD_WIDTH] / 1000:.2f}")

            if "barrier_height" in geom:
                _set(median_height, f"{geom['barrier_height'] / 1000:.2f}")
            elif "kerb_height" in geom:
                _set(median_height, f"{geom['kerb_height'] / 1000:.2f}")

            if median_width and median_height:
                try:
                    w = float(median_width.text())
                    h = float(median_height.text())
                    _set(median_area, f"{w * h:.2f}")
                except:
                    pass
            self._auto_compute_median_load()
        elif is_metallic:
            if median_post_spacing:
                _set(median_post_spacing, "1")
            if force and median_load:
                median_load.clear()
        elif is_custom:
            if geom:
                if KEY_MD_WIDTH in geom:
                    _set(median_width, f"{geom[KEY_MD_WIDTH] / 1000:.2f}")
                if "barrier_height" in geom:
                    _set(median_height, f"{geom['barrier_height'] / 1000:.2f}")
                elif "kerb_height" in geom:
                    _set(median_height, f"{geom['kerb_height'] / 1000:.2f}")
            if force and median_load:
                median_load.clear()

        self._update_median_visibility(median_type, include_median=True)

        geom = MedianGeometry.get_geometry(effective_median_type)

        params = {
            KEY_MD_TYPE: median_type,
        }

        if geom:
            if KEY_MD_WIDTH in geom:
                params[KEY_MD_WIDTH] = geom[KEY_MD_WIDTH]

            if "barrier_height" in geom:
                params[KEY_MD_HEIGHT] = geom["barrier_height"]
            elif "kerb_height" in geom:
                params[KEY_MD_HEIGHT] = geom["kerb_height"]

            self.cad_preview.update_params(params)
            
        if hasattr(self, "cad_preview"):
            params = {
                "median_present": True,
                KEY_MD_TYPE: median_type,
            }

            if median_width and median_width.text():
                params[KEY_MD_WIDTH] = float(median_width.text()) * 1000

            if median_height and median_height.text():
                params[KEY_MD_HEIGHT] = float(median_height.text()) * 1000

            self.cad_preview.update_params(params)

    def on_median_type_changed(self, median_type):
        print(f"Median type changed to: {median_type}")
        self._apply_median_defaults(median_type, force=True)

        if hasattr(self, "cad_preview"):
            params = {KEY_MD_TYPE: median_type}
            self.cad_preview.update_params(params)

        self.recalculate_girders()
        

    # ----- Railing sub-tab -----------------------------------------------------

    def _effective_railing_type(self, railing_type):
        return "IRC 5 - RCC Railing" if railing_type == "Custom" else railing_type

    def _apply_railing_defaults(self, force: bool = False):
        railing_type_w = self._find_railing_widget(KEY_RL_TYPE)
        if not railing_type_w:
            return

        railing_type = railing_type_w.currentText()
        effective_railing_type = self._effective_railing_type(railing_type)
        geom = RailingGeometry.get_geometry(effective_railing_type)

        railing_width = self._find_railing_widget(KEY_RL_WIDTH)
        railing_height = self._find_railing_widget(KEY_RL_HEIGHT)
        railing_load_mode = self._find_railing_widget(KEY_RL_LOAD_MODE)

        def _set(widget, value: str):
            if widget is None:
                return
            if force or not widget.text():
                widget.setText(value)

        if geom:
            if "width" in geom:
                _set(railing_width, f"{geom['width']:.0f}")

            if "height" in geom:
                _set(railing_height, f"{geom['height'] / 1000:.2f}")

        # Grey out fixed parameters per IRC 5
        is_custom = railing_type == "Custom"
        if railing_width:
            railing_width.setEnabled(is_custom)
        if railing_height:
            railing_height.setEnabled(is_custom)
        if railing_load_mode:
            railing_load_mode.setEnabled(is_custom)

        if railing_load_mode:
            railing_load_mode.blockSignals(True)
            railing_load_mode.setCurrentText("As per IRC 6")
            railing_load_mode.blockSignals(False)

            # Manually apply once
            self.on_railing_load_mode_changed("As per IRC 6")

        geom = RailingGeometry.get_geometry(effective_railing_type)

        params = {
            KEY_RL_TYPE: railing_type,
        }

        if geom:
            if "height" in geom:
                params["railing_height"] = geom["height"]

            if "width" in geom:
                params["railing_width"] = geom["width"]

            self.cad_preview.update_params(params)

    def on_railing_type_changed(self, railing_type):
        print(f"Railing type changed to: {railing_type}")
        self._apply_railing_defaults(force=True)

        if hasattr(self, "cad_preview"):
            params = {KEY_RL_TYPE: railing_type}
            self.cad_preview.update_params(params)

        self.recalculate_girders()

    def on_railing_load_mode_changed(self, mode):
        railing_load_value = self._find_railing_widget(KEY_RL_LOAD_VALUE)
        if not railing_load_value:
            return
        is_auto = mode.startswith("As per") or mode.startswith("Automatic")
        if is_auto:
            railing_load_value.setReadOnly(True)
            railing_load_value.setEnabled(True)
            railing_load_value.setText("1.5")
            railing_load_value.setPlaceholderText("")
            # Subtle disabled styling for auto mode
            railing_load_value.setStyleSheet(
                "QLineEdit { background-color: #f1f1f1; color: #7a7a7a;"
                " border: 1px solid #bfbfbf; border-radius: 4px; padding: 4px 6px; }"
            )
        else:
            # User-defined mode - allow user to enter value
            railing_load_value.setReadOnly(False)
            railing_load_value.setEnabled(True)
            railing_load_value.clear()
            railing_load_value.setPlaceholderText("Enter load value")
            # Restore normal styling
            railing_load_value.setStyleSheet(
                "QLineEdit { background-color: #ffffff; color: #000000;"
                " border: 1px solid #000000; border-radius: 4px; padding: 4px 6px; }"
            )

    def validate_railing_height(self):
        try:
            railing_height = self._find_railing_widget(KEY_RL_HEIGHT)
            if railing_height and railing_height.text():
                height = float(railing_height.text())
                if height < MIN_RAILING_HEIGHT:
                    CustomMessageBox(
                        title="Railing Height Error",
                        text=f"Railing height must be at least {MIN_RAILING_HEIGHT} m as per IRC 5 Clauses 109.7.2.3 and 109.7.2.4.",
                        buttons=["OK"],
                        dialogType=MessageBoxType.Critical,
                    ).exec()
        except:
            pass


    # ----- Wearing Course sub-tab ----------------------------------------------

    def on_wearing_material_changed(self, material):
        wearing_density = self._find_wearing_widget(KEY_WC_DENSITY)
        wearing_thickness = self._find_wearing_widget(KEY_WC_THICKNESS)
        if not wearing_density or not wearing_thickness:
            return
        # Defaults per material; allow user edits afterward
        if material == "Concrete":
            wearing_density.setText("24.0")
        elif material == "Bituminous":
            wearing_density.setText("22.0")
        else:
            wearing_density.clear()

        # Grey out density for fixed-density materials; enable for Other and Custom
        wearing_density.setEnabled(material not in ("Concrete", "Bituminous"))

        if not wearing_thickness.text():
            wearing_thickness.setText("50")
    # ----- Lane Details sub-tab ------------------------------------------------

    _LANE_WIDTH_M = 3.5  # IRC 5 Clause 104.3.1 minimum design lane width

    def update_carriageway_width(self, carriageway_width):
        """Called by the parent before showing the dialog when carriageway width has changed."""
        if carriageway_width and carriageway_width != self.carriageway_width:
            self.carriageway_width = carriageway_width
            self._initialize_lane_defaults()

    def _initialize_lane_defaults(self):
        """Populate combo + table with IRC 5 Clause 104.3.1 defaults on first open."""
        lane_count_combo = self._find_lane_widget(KEY_WC_LD_LANE_TABLE_COUNT, QComboBox)
        lane_table       = self._find_lane_widget(KEY_WC_LD_LANE_TABLE, QTableWidget)
        if not lane_count_combo or not lane_table:
            return

        try:
            max_allowed = max(1, min(6, int(math.floor(
                float(self.carriageway_width) / self._LANE_WIDTH_M
            ))))
        except Exception:
            max_allowed = 1

        self._updating_lane_table = True
        try:
            lane_count_combo.blockSignals(True)
            lane_count_combo.clear()
            for i in range(1, max_allowed + 1):
                lane_count_combo.addItem(str(i))
            lane_count_combo.setCurrentText(str(max_allowed))
            lane_count_combo.blockSignals(False)
            self._reset_lane_rows(lane_table, max_allowed)
            self._fill_lane_defaults(lane_table, max_allowed)
        finally:
            self._updating_lane_table = False

        if not self._lane_cell_signal_connected:
            try:
                lane_table.cellChanged.connect(self._on_lane_cell_changed)
                self._lane_cell_signal_connected = True
            except Exception:
                pass

    def _reset_lane_rows(self, lane_table, num_lanes):
        """Resize the table and stamp lane-number items in column 0."""
        lane_table.setRowCount(num_lanes)
        for i in range(num_lanes):
            num_item = QTableWidgetItem(str(i + 1))
            num_item.setFlags(num_item.flags() & ~Qt.ItemIsEditable)
            num_item.setTextAlignment(Qt.AlignCenter)
            lane_table.setItem(i, 0, num_item)
            for col in (1, 2):
                cell = QTableWidgetItem("")
                cell.setTextAlignment(Qt.AlignCenter)
                lane_table.setItem(i, col, cell)

    def _fill_lane_defaults(self, lane_table, lane_count):
        """Write default start positions and widths (IRC 5: 3.5 m each)."""
        start = 0.0
        for i in range(lane_count):
            self._set_cell(lane_table, i, 1, f"{start:.2f}")
            self._set_cell(lane_table, i, 2, f"{self._LANE_WIDTH_M:.2f}")
            start += self._LANE_WIDTH_M

    def _set_cell(self, lane_table, row, col, text):
        """Write text into a table cell, creating the item if needed."""
        item = lane_table.item(row, col)
        if item is None:
            item = QTableWidgetItem()
            item.setTextAlignment(Qt.AlignCenter)
            lane_table.setItem(row, col, item)
        item.setText(text)

    def _recompute_lane_starts(self):
        """Recompute cumulative start positions from current widths; warn if total > carriageway."""
        lane_table = self._find_lane_widget(KEY_WC_LD_LANE_TABLE, QTableWidget)
        if not lane_table or lane_table.rowCount() == 0:
            return

        start = 0.0
        total = 0.0
        self._updating_lane_table = True
        try:
            for i in range(lane_table.rowCount()):
                item = lane_table.item(i, 2)
                try:
                    w = float(item.text()) if item and item.text() else self._LANE_WIDTH_M
                except ValueError:
                    w = self._LANE_WIDTH_M
                if w < self._LANE_WIDTH_M:
                    w = self._LANE_WIDTH_M
                    self._set_cell(lane_table, i, 2, f"{w:.2f}")
                self._set_cell(lane_table, i, 1, f"{start:.2f}")
                start += w
                total += w
        finally:
            self._updating_lane_table = False

        try:
            carriageway = float(self.carriageway_width) if self.carriageway_width else None
        except Exception:
            carriageway = None
        if carriageway and total - carriageway > 1e-6:
            CustomMessageBox(
                title="Lane Width Exceeds Carriageway",
                text=f"Sum of lane widths ({total:.2f} m) exceeds carriageway width ({carriageway:.2f} m).\n"
                      "Adjust lane count or widths per IRC 5 Clause 104.3.1.",
                buttons=["OK"],
                dialogType=MessageBoxType.Warning,
            ).exec()

    def _on_lane_cell_changed(self, row, column):
        """Validate the edited cell and recompute start positions."""
        if self._updating_lane_table:
            return
        lane_table = self._find_lane_widget(KEY_WC_LD_LANE_TABLE, QTableWidget)
        if not lane_table:
            return

        if column == 2:
            # Validate width >= IRC minimum
            item = lane_table.item(row, 2)
            try:
                w = float(item.text()) if item and item.text() else None
            except ValueError:
                w = None
            if w is None or w + 1e-6 < self._LANE_WIDTH_M:
                if w is not None:
                    CustomMessageBox(
                        title="Lane Width Below IRC Minimum",
                        text=f"IRC 5 Clause 104.3.1 requires a lane width of at least {self._LANE_WIDTH_M:.2f} m.",
                        buttons=["OK"],
                        dialogType=MessageBoxType.Critical,
                    ).exec()
                self._set_cell(lane_table, row, 2, f"{self._LANE_WIDTH_M:.2f}")

        elif column == 1:
            # Validate start position continuity
            item = lane_table.item(row, 1)
            try:
                start = float(item.text()) if item and item.text() else None
            except ValueError:
                start = None

            if start is None:
                self._recompute_lane_starts()
                return
            if row == 0:
                if abs(start) > 1e-6:
                    CustomMessageBox(
                        title="Lane Start Offset",
                        text="First lane must start at 0 m from inner edge of crash barrier.",
                        buttons=["OK"],
                        dialogType=MessageBoxType.Warning,
                    ).exec()
                    self._recompute_lane_starts()
                return
            prev_s_item = lane_table.item(row - 1, 1)
            prev_w_item = lane_table.item(row - 1, 2)
            prev_s = float(prev_s_item.text()) if prev_s_item and prev_s_item.text() else 0.0
            prev_w = float(prev_w_item.text()) if prev_w_item and prev_w_item.text() else self._LANE_WIDTH_M
            if abs(start - (prev_s + prev_w)) > 1e-3:
                CustomMessageBox(
                    title="Lane Start Sequence",
                    text="Each lane start must equal previous lane start plus previous lane width.",
                    buttons=["OK"],
                    dialogType=MessageBoxType.Warning,
                ).exec()
                self._recompute_lane_starts()
                return

        self._recompute_lane_starts()

    def on_lane_count_changed(self, text):
        """Handle lane count combo change — resize table and fill defaults."""
        if self._updating_lane_table:
            return
        try:
            num_lanes = int(text)
        except (TypeError, ValueError):
            return
        lane_table = self._find_lane_widget(KEY_WC_LD_LANE_TABLE, QTableWidget)
        if lane_table:
            self._reset_lane_rows(lane_table, num_lanes)
            self._fill_lane_defaults(lane_table, num_lanes)

    # --------------------- Lane Details sub-tab functionality  END   ---------------------


    # ----- Global reset --------------------------------------------------------

    def reset_defaults(self):
        # Layout defaults
        if hasattr(self, "girder_spacing"):
            self.girder_spacing.setText(f"{DEFAULT_GIRDER_SPACING:.2f}")
        if hasattr(self, "deck_overhang"):
            self.deck_overhang.setText(f"{0.35 * DEFAULT_GIRDER_SPACING:.2f}")
        if hasattr(self, "no_of_girders"):
            self.no_of_girders.setText("2")
        self._clear_adjust_notice()
        self._solve_layout("spacing")

        # Crash barrier defaults
        self._reset_crash_barrier_defaults()

        # Median defaults
        median_type_w = self._find_median_widget(KEY_MD_TYPE)
        if median_type_w:
            median_type_w.setCurrentText("IRC 5 - Raised Kerb")
            self._apply_median_defaults(median_type_w.currentText(), force=True)

        # Railing defaults
        railing_type_w = self._find_railing_widget(KEY_RL_TYPE)
        if railing_type_w:
            railing_type_w.setCurrentText("IRC 5 - RCC Railing")
            self._apply_railing_defaults(force=True)

        # Wearing course defaults
        wearing_material_w = self._find_wearing_widget(KEY_WC_MATERIAL)
        if wearing_material_w:
            wearing_material_w.setCurrentText("Concrete")
            self.on_wearing_material_changed(wearing_material_w.currentText())
        wearing_thickness_w = self._find_wearing_widget(KEY_WC_THICKNESS)
        if wearing_thickness_w and not wearing_thickness_w.text():
            wearing_thickness_w.setText("50")