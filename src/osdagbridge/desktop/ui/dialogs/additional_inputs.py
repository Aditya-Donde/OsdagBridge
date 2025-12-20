"""
Additional Inputs Widget for Highway Bridge Design
Provides detailed input fields for manual bridge parameter definition
"""
import sys
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QTabBar, QLabel, QLineEdit,
    QComboBox, QGroupBox, QFormLayout, QPushButton, QScrollArea,
    QCheckBox, QMessageBox, QSizePolicy, QSpacerItem, QStackedWidget,
    QFrame, QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QTextEdit, QDialog, QSizePolicy, QSizeGrip
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QDoubleValidator, QIntValidator

from osdagbridge.core.utils.common import *
from osdagbridge.desktop.ui.utils.custom_titlebar import CustomTitleBar
from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style, create_action_button_bar
from osdagbridge.desktop.ui.dialogs.tabs.typical_section_details import TypicalSectionDetailsTab
from osdagbridge.desktop.ui.dialogs.tabs.optimizable_field import OptimizableField
from osdagbridge.desktop.ui.dialogs.tabs.section_properties_tab import SectionPropertiesTab
from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.section_properties.girder_details_tab import GirderDetailsTab
from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.section_properties.stiffener_details_tab import StiffenerDetailsTab
from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.section_properties.cross_bracing_details_tab import CrossBracingDetailsTab
from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.section_properties.end_diaphragm_details_tab import EndDiaphragmDetailsTab
from osdagbridge.desktop.ui.dialogs.tabs.custom_vehicle_dialog import CustomVehicleDialog
from osdagbridge.desktop.ui.dialogs.tabs.loading_tab import LoadingTab

# =================================================================================
#   MAIN IMPLEMENTATION
# =================================================================================

class AdditionalInputs(QDialog):
    """Main dialog for Additional Inputs with tabbed interface"""
    
    def __init__(self, footpath_value="None", carriageway_width=7.5, parent=None):
        super().__init__(parent)
        self.setObjectName("AdditionalInputs")
        self.resize(1024, 720)
        self.setMinimumSize(900, 520)
        self.setSizeGripEnabled(True)
        self.footpath_value = footpath_value
        self.carriageway_width = carriageway_width
        self.init_ui()
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                border: 1px solid #90AF13;
            }
        """)

    def setupWrapper(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowSystemMenuHint)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(0)
        
        self.title_bar = CustomTitleBar()
        self.title_bar.setTitle("Additional Inputs")
        main_layout.addWidget(self.title_bar)
        
        self.content_widget = QWidget(self)
        main_layout.addWidget(self.content_widget, 1)

        size_grip = QSizeGrip(self)
        size_grip.setFixedSize(16, 16)

        overlay = QHBoxLayout()
        overlay.setContentsMargins(0, 0, 4, 4)
        overlay.addStretch(1)
        overlay.addWidget(size_grip, 0, Qt.AlignBottom | Qt.AlignRight)
        main_layout.addLayout(overlay)
    
    def init_ui(self):
        self.setupWrapper()
        
        main_layout = QVBoxLayout(self.content_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Main tab widget
        self.tabs = QTabWidget()
        self.tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.stretching_tab_bar = QTabBar()
        self.stretching_tab_bar.setElideMode(Qt.ElideRight)
        self.tabs.setTabBar(self.stretching_tab_bar)
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #d1d1d1;
                background-color: #ffffff;
                border-radius: 6px;
            }
            QTabBar::tab {
                font-weight: bold;
                font-size: 12px;
                background: #ffffff;
                color: #3a3a3a;
                border: 1px solid #d1d1d1;
                padding: 10px 22px;
            }
            QTabBar::tab:selected {
                background: #90AF13;
                color: #ffffff;
                border: 1px solid #90AF13;
            }
            QTabBar::tab:hover {
                background: #90AF13;
                color: #ffffff;
            }
        """)
        
        # Sub-Tab 1: Typical Section Details
        self.typical_section_tab = TypicalSectionDetailsTab(self.footpath_value, self.carriageway_width)
        self.tabs.addTab(self.typical_section_tab, "Typical Section Details")
        
        # Sub-Tab 2: Member Properties
        self.section_properties_tab = SectionPropertiesTab()
        self.tabs.addTab(self.section_properties_tab, "Member Properties")
        
        # Sub-Tab 3: Loading
        self.loading_tab = LoadingTab()
        self.tabs.addTab(self.loading_tab, "Loading")
        
        # Sub-Tab 4: Support Conditions
        support_tab = self._build_support_conditions_tab()
        self.tabs.addTab(support_tab, "Support Conditions")
        
        # Sub-Tab 5: Analysis/Design Options
        design_options_tab = self._build_design_options_tab()
        self.tabs.addTab(design_options_tab, "Analysis/Design Options")
        
        # Sub-Tab 6: Design Options (Cont.)
        analysis_design_tab = self._build_design_options_cont_tab()
        self.tabs.addTab(analysis_design_tab, "Design Options (Cont.)")
        
        main_layout.addWidget(self.tabs)
        

        action_bar, self.defaults_button, self.save_button = create_action_button_bar()
        self.defaults_button.clicked.connect(lambda: self._show_placeholder_message("Defaults"))
        self.save_button.clicked.connect(lambda: self._show_placeholder_message("Save"))
        main_layout.addSpacing(6)
        main_layout.addWidget(action_bar)

    def _show_placeholder_message(self, action_name):
        """Show placeholder message for action buttons"""
        QMessageBox.information(self, action_name, "This action will be available in an upcoming update.")

    def _build_support_conditions_tab(self):
        """Build the Support Conditions tab matching reference design"""
        widget = QWidget()
        widget.setStyleSheet("background-color: #f5f5f5;")
        
        main_layout = QVBoxLayout(widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        # Main card
        card = QFrame()
        card.setStyleSheet("QFrame { border: 1px solid #b2b2b2; border-radius: 10px; background-color: #ffffff; }")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(16)

        label_style = "font-size: 11px; color: #3a3a3a; background: transparent; border: none;"
        heading_style = "font-size: 12px; font-weight: 700; color: #2b2b2b; background: transparent; border: none;"
        field_width = 120

        # Support Condition section
        support_title = QLabel("Support Condition*")
        support_title.setStyleSheet(heading_style)
        card_layout.addWidget(support_title)

        support_grid = QGridLayout()
        support_grid.setContentsMargins(0, 8, 0, 0)
        support_grid.setHorizontalSpacing(12)
        support_grid.setVerticalSpacing(12)
        support_grid.setColumnMinimumWidth(0, 120)

        # Left Support
        lbl = QLabel("Left Support:")
        lbl.setStyleSheet(label_style)
        self.left_support_combo = QComboBox()
        self.left_support_combo.addItems(["Fixed", "Pinned", "Roller"])
        self.left_support_combo.setFixedWidth(field_width)
        apply_field_style(self.left_support_combo)
        support_grid.addWidget(lbl, 0, 0, Qt.AlignLeft | Qt.AlignVCenter)
        support_grid.addWidget(self.left_support_combo, 0, 1, Qt.AlignLeft)

        # Right Support
        lbl = QLabel("Right Support:")
        lbl.setStyleSheet(label_style)
        self.right_support_combo = QComboBox()
        self.right_support_combo.addItems(["Fixed", "Pinned", "Roller"])
        self.right_support_combo.setFixedWidth(field_width)
        apply_field_style(self.right_support_combo)
        support_grid.addWidget(lbl, 1, 0, Qt.AlignLeft | Qt.AlignVCenter)
        support_grid.addWidget(self.right_support_combo, 1, 1, Qt.AlignLeft)

        card_layout.addLayout(support_grid)

        # Bearing Length section
        bearing_title = QLabel("Bearing length*")
        bearing_title.setStyleSheet(heading_style)
        card_layout.addWidget(bearing_title)

        bearing_grid = QGridLayout()
        bearing_grid.setContentsMargins(0, 8, 0, 0)
        bearing_grid.setHorizontalSpacing(12)
        bearing_grid.setVerticalSpacing(12)
        bearing_grid.setColumnMinimumWidth(0, 120)

        lbl = QLabel("Bearing Length Value")
        lbl.setStyleSheet(label_style)
        self.bearing_length_input = QLineEdit()
        self.bearing_length_input.setText("0")
        self.bearing_length_input.setFixedWidth(field_width)
        apply_field_style(self.bearing_length_input)
        bearing_grid.addWidget(lbl, 0, 0, Qt.AlignLeft | Qt.AlignVCenter)
        bearing_grid.addWidget(self.bearing_length_input, 0, 1, Qt.AlignLeft)

        card_layout.addLayout(bearing_grid)
        card_layout.addStretch()

        main_layout.addWidget(card)
        main_layout.addStretch()

        return widget

    def _build_design_options_tab(self):
        """Build the Design Options tab matching reference design"""
        widget = QWidget()
        widget.setStyleSheet("background-color: #f5f5f5;")
        
        main_layout = QVBoxLayout(widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)
        card_style = "QFrame { border: 1px solid #b2b2b2; border-radius: 8px; background-color: #ffffff; }"
        label_style = "font-size: 11px; color: #3a3a3a; background: transparent; border: none;"
        heading_style = "font-size: 12px; font-weight: 700; color: #2b2b2b; background: transparent; border: none;"
        field_width = 150

        # Construction Stage card
        construction_card = QFrame()
        construction_card.setStyleSheet(card_style)
        construction_layout = QVBoxLayout(construction_card)
        construction_layout.setContentsMargins(16, 14, 16, 14)
        construction_layout.setSpacing(10)

        construction_title = QLabel("Construction Stage:")
        construction_title.setStyleSheet(heading_style)
        construction_layout.addWidget(construction_title)

        construction_grid = QGridLayout()
        construction_grid.setContentsMargins(0, 4, 0, 0)
        construction_grid.setHorizontalSpacing(12)
        construction_grid.setVerticalSpacing(8)
        construction_grid.setColumnMinimumWidth(0, 130)

        lbl = QLabel("Included:")
        lbl.setStyleSheet(label_style)
        self.construction_stage_combo = QComboBox()
        self.construction_stage_combo.addItems(["Yes", "No"])
        self.construction_stage_combo.setFixedWidth(field_width)
        apply_field_style(self.construction_stage_combo)
        construction_grid.addWidget(lbl, 0, 0, Qt.AlignLeft | Qt.AlignVCenter)
        construction_grid.addWidget(self.construction_stage_combo, 0, 1, Qt.AlignLeft)

        construction_layout.addLayout(construction_grid)
        main_layout.addWidget(construction_card)

        # Deck and Shear Studs card
        design_card = QFrame()
        design_card.setStyleSheet(card_style)
        design_layout = QVBoxLayout(design_card)
        design_layout.setContentsMargins(16, 16, 16, 16)
        design_layout.setSpacing(14)

        deck_title = QLabel("Deck Design:")
        deck_title.setStyleSheet(heading_style)
        design_layout.addWidget(deck_title)

        deck_grid = QGridLayout()
        deck_grid.setContentsMargins(0, 2, 0, 0)
        deck_grid.setHorizontalSpacing(12)
        deck_grid.setVerticalSpacing(10)
        deck_grid.setColumnMinimumWidth(0, 150)

        lbl = QLabel("Reinforcement Size:")
        lbl.setStyleSheet(label_style)
        self.reinforcement_size_combo = QComboBox()
        self.reinforcement_size_combo.addItems(["8 mm", "10 mm", "12 mm", "16 mm", "20 mm"])
        self.reinforcement_size_combo.setFixedWidth(field_width)
        apply_field_style(self.reinforcement_size_combo)
        deck_grid.addWidget(lbl, 0, 0, Qt.AlignLeft | Qt.AlignVCenter)
        deck_grid.addWidget(self.reinforcement_size_combo, 0, 1, Qt.AlignLeft)

        lbl = QLabel("Reinforcement Material:")
        lbl.setStyleSheet(label_style)
        self.reinforcement_material_combo = QComboBox()
        self.reinforcement_material_combo.addItems(["Fe 415", "Fe 500", "Fe 550"])
        self.reinforcement_material_combo.setFixedWidth(field_width)
        apply_field_style(self.reinforcement_material_combo)
        deck_grid.addWidget(lbl, 1, 0, Qt.AlignLeft | Qt.AlignVCenter)
        deck_grid.addWidget(self.reinforcement_material_combo, 1, 1, Qt.AlignLeft)

        design_layout.addLayout(deck_grid)

        shear_title = QLabel("Shear Studs:")
        shear_title.setStyleSheet(heading_style)
        design_layout.addWidget(shear_title)

        shear_grid = QGridLayout()
        shear_grid.setContentsMargins(0, 2, 0, 0)
        shear_grid.setHorizontalSpacing(12)
        shear_grid.setVerticalSpacing(10)
        shear_grid.setColumnMinimumWidth(0, 150)

        lbl = QLabel("Material:")
        lbl.setStyleSheet(label_style)
        self.shear_stud_material_input = QLineEdit()
        self.shear_stud_material_input.setFixedWidth(field_width)
        apply_field_style(self.shear_stud_material_input)
        shear_grid.addWidget(lbl, 0, 0, Qt.AlignLeft | Qt.AlignVCenter)
        shear_grid.addWidget(self.shear_stud_material_input, 0, 1, Qt.AlignLeft)

        lbl = QLabel("Diameter (mm):")
        lbl.setStyleSheet(label_style)
        self.shear_stud_diameter_input = QLineEdit()
        self.shear_stud_diameter_input.setFixedWidth(field_width)
        apply_field_style(self.shear_stud_diameter_input)
        shear_grid.addWidget(lbl, 1, 0, Qt.AlignLeft | Qt.AlignVCenter)
        shear_grid.addWidget(self.shear_stud_diameter_input, 1, 1, Qt.AlignLeft)

        lbl = QLabel("Height (mm):")
        lbl.setStyleSheet(label_style)
        self.shear_stud_height_input = QLineEdit()
        self.shear_stud_height_input.setFixedWidth(field_width)
        apply_field_style(self.shear_stud_height_input)
        shear_grid.addWidget(lbl, 2, 0, Qt.AlignLeft | Qt.AlignVCenter)
        shear_grid.addWidget(self.shear_stud_height_input, 2, 1, Qt.AlignLeft)

        design_layout.addLayout(shear_grid)
        design_layout.addStretch()

        main_layout.addWidget(design_card)
        main_layout.addStretch()

        return widget

    def _build_design_options_cont_tab(self):
        """Build the Design Options (Cont.) tab to match provided layout"""
        widget = QWidget()
        widget.setStyleSheet("background-color: #f5f5f5;")

        # Use scroll area to prevent overlap
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: #f5f5f5;")
        main_layout = QVBoxLayout(scroll_content)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        label_style = "font-size: 11px; color: #333333; background: transparent; border: none;"
        
        # Helper to create a pill-shaped frame
        def create_pill_frame():
            frame = QFrame()
            frame.setStyleSheet("QFrame { border: 1px solid #a0a0a0; border-radius: 16px; background-color: #ffffff; }")
            return frame

        # --- Top Grid (Gamma factors) - no frame, just rows ---
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(20)
        grid.setVerticalSpacing(8)
        grid.setColumnMinimumWidth(0, 300)
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 0)

        def add_row(row, text, attr_name):
            lbl = QLabel(text)
            lbl.setStyleSheet(label_style)
            lbl.setMinimumHeight(24)
            line = QLineEdit()
            line.setFixedSize(140, 26)
            apply_field_style(line)
            grid.addWidget(lbl, row, 0, Qt.AlignLeft | Qt.AlignVCenter)
            grid.addWidget(line, row, 1, Qt.AlignLeft | Qt.AlignVCenter)
            setattr(self, attr_name, line)

        add_row(0, "Concrete basic & seismic(Gamma_C)", "gamma_c_basic_input")
        add_row(1, "Concrete Accidental (Gamma_C)", "gamma_c_accidental_input")
        add_row(2, "Structural steel for Yielding and Buckling(Gamma_M0)", "gamma_m0_input")
        add_row(3, "Structural Steel For Ultimate Stress(Gamme_M1)", "gamma_m1_input")
        add_row(4, "Reinforcing Steel (Gamma_s)", "gamma_s_input")
        add_row(5, "Shear Connectors For Yield(Gamma_v)", "gamma_v_input")
        add_row(6, "Fatigue Load(Gamma_flt)", "gamma_flt_input")
        add_row(7, "Fatigue Strength(Gamma_Mf, t)", "gamma_mf_input")

        main_layout.addLayout(grid)
        main_layout.addSpacing(8)

        # --- Number of load cycles in pill frame ---
        cycles_frame = create_pill_frame()
        cycles_frame.setFixedHeight(38)
        cycles_layout = QHBoxLayout(cycles_frame)
        cycles_layout.setContentsMargins(16, 6, 16, 6)
        cycles_layout.setSpacing(10)
        cycles_label = QLabel("Number of Load Cycles(Cl605.3,Cl605.4)")
        cycles_label.setStyleSheet(label_style)
        cycles_layout.addWidget(cycles_label)
        cycles_layout.addStretch()
        main_layout.addWidget(cycles_frame)

        # --- Wide input below load cycles ---
        self.load_cycles_input = QLineEdit()
        self.load_cycles_input.setFixedHeight(30)
        apply_field_style(self.load_cycles_input)
        main_layout.addWidget(self.load_cycles_input)

        # --- K factors row 1 in pill frame ---
        k1_frame = create_pill_frame()
        k1_frame.setFixedHeight(42)
        k1_layout = QHBoxLayout(k1_frame)
        k1_layout.setContentsMargins(16, 6, 16, 6)
        k1_layout.setSpacing(16)
        for label, attr in [("K1:", "k1_input"), ("K3:", "k3_input"), ("K4:", "k4_input"), ("K6:", "k6_input")]:
            lbl = QLabel(label)
            lbl.setStyleSheet(label_style)
            line = QLineEdit()
            line.setFixedSize(80, 26)
            apply_field_style(line)
            setattr(self, attr, line)
            k1_layout.addWidget(lbl)
            k1_layout.addWidget(line)
        k1_layout.addStretch()
        main_layout.addWidget(k1_frame)

        # --- Limit row in pill frame ---
        limit_frame = create_pill_frame()
        limit_frame.setFixedHeight(42)
        limit_layout = QHBoxLayout(limit_frame)
        limit_layout.setContentsMargins(16, 6, 16, 6)
        limit_layout.setSpacing(16)
        limit_lbl = QLabel("Limit : L")
        limit_lbl.setStyleSheet(label_style)
        self.limit_input = QLineEdit()
        self.limit_input.setFixedSize(120, 26)
        apply_field_style(self.limit_input)
        unit_lbl = QLabel("m")
        unit_lbl.setStyleSheet(label_style)
        limit_layout.addWidget(limit_lbl)
        limit_layout.addWidget(self.limit_input)
        limit_layout.addWidget(unit_lbl)
        limit_layout.addStretch()
        main_layout.addWidget(limit_frame)

        # --- K factors row 2 with exposure in pill frame ---
        k2_frame = create_pill_frame()
        k2_frame.setFixedHeight(42)
        k2_layout = QHBoxLayout(k2_frame)
        k2_layout.setContentsMargins(16, 6, 16, 6)
        k2_layout.setSpacing(16)
        for label, attr in [("K3:", "k3_second_input"), ("K4:", "k4_second_input")]:
            lbl = QLabel(label)
            lbl.setStyleSheet(label_style)
            line = QLineEdit()
            line.setFixedSize(80, 26)
            apply_field_style(line)
            setattr(self, attr, line)
            k2_layout.addWidget(lbl)
            k2_layout.addWidget(line)
        exposure_lbl = QLabel("Exposure:")
        exposure_lbl.setStyleSheet(label_style)
        self.exposure_input = QLineEdit()
        self.exposure_input.setFixedSize(100, 26)
        apply_field_style(self.exposure_input)
        k2_layout.addWidget(exposure_lbl)
        k2_layout.addWidget(self.exposure_input)
        k2_layout.addStretch()
        main_layout.addWidget(k2_frame)

        # --- Post-buckling checkbox in pill frame ---
        cb_frame = create_pill_frame()
        cb_frame.setFixedHeight(42)
        cb_layout = QHBoxLayout(cb_frame)
        cb_layout.setContentsMargins(16, 6, 16, 6)
        self.post_buckling_checkbox = QCheckBox("Post-buckling Tension Field Action for Shear Resistance")
        self.post_buckling_checkbox.setStyleSheet("QCheckBox { font-size: 11px; color: #333333; background: transparent; spacing: 8px; }")
        cb_layout.addWidget(self.post_buckling_checkbox)
        cb_layout.addStretch()
        main_layout.addWidget(cb_frame)

        main_layout.addSpacing(8)

        # --- Limit state groups side by side ---
        groups_layout = QHBoxLayout()
        groups_layout.setSpacing(20)

        def build_group(title, items):
            box = QGroupBox(title)
            box.setStyleSheet(
                "QGroupBox { border: 1px solid #b0b0b0; border-radius: 6px; margin-top: 12px; padding: 8px; background: #ffffff; }"
                "QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; left: 12px; padding: 0 6px; background: #f5f5f5; font-weight: 600; font-size: 11px; color: #333333; }"
            )
            vbox = QVBoxLayout(box)
            vbox.setContentsMargins(16, 24, 16, 16)
            vbox.setSpacing(12)
            checkboxes = []
            for text in items:
                cb = QCheckBox(text)
                cb.setStyleSheet("QCheckBox { font-size: 11px; color: #333333; background: transparent; spacing: 8px; }")
                vbox.addWidget(cb)
                checkboxes.append(cb)
            return box, checkboxes

        ultimate_items = [
            "Bending Resistance",
            "Resistance to Vertical Shear",
            "Resistance to Lateral-torsional Buckling",
            "Resistance to Transverse force",
            "Resistance to Longitudinal Shear",
            "Resistance to Fatigue",
        ]
        service_items = [
            "Stress Limitation",
            "Longitudinal Shear (SLS)",
            "Deflection Control",
            "Crack Width Check",
        ]

        ultimate_box, self.ultimate_checkboxes = build_group("Ultimate Limit States", ultimate_items)
        service_box, self.service_checkboxes = build_group("Serviceability Limit States", service_items)

        groups_layout.addWidget(ultimate_box)
        groups_layout.addWidget(service_box)

        main_layout.addLayout(groups_layout)
        main_layout.addStretch()

        scroll.setWidget(scroll_content)
        
        outer_layout = QVBoxLayout(widget)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(scroll)

        return widget
    
    def update_footpath_value(self, footpath_value):
        """Update footpath value across all tabs"""
        self.footpath_value = footpath_value
        self.typical_section_tab.update_footpath_value(footpath_value)
