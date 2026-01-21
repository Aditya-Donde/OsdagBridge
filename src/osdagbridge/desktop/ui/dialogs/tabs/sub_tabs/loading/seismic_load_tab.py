from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QLineEdit,
    QFrame,
    QGridLayout,
    QCheckBox,
    QScrollArea,
)

from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style

IRC_SEISMIC_DEFAULTS = {
    "seismic_zone": "II",
    "importance_factor": "1.0",
    "soil_type": "Type I – Rocky or Hard Soil",
    "damping": "2",
    "response_reduction_factor": "1",
    "dead_load_mode": "Automatic",
    "live_load_mode": "Automatic",
}

# STANDARDIZED DIMENSIONS - Define once, use everywhere
FIELD_WIDTH = 180
FIELD_HEIGHT = 28
LABEL_MIN_WIDTH = 220


class SeismicLoadTab(QWidget):
    """Seismic/Earthquake Load tab content extracted from LoadingTab."""

    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self._build_ui()

    def _build_ui(self):
        owner = self.owner

        self.setStyleSheet("background-color: #f5f5f5;")
        
        # Main layout with scroll area
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet("QScrollArea { background-color: #f5f5f5; border: none; }")

        # Scrollable content widget
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: #f5f5f5;")
        page_layout = QVBoxLayout(scroll_content)
        page_layout.setContentsMargins(12, 12, 12, 12)
        page_layout.setSpacing(12)

        content_row = QHBoxLayout()
        content_row.setContentsMargins(0, 0, 0, 0)
        content_row.setSpacing(16)

        # ============ LEFT CARD ============
        left_card = owner._create_card()
        left_card.setStyleSheet("QFrame { border: 1px solid #b2b2b2; border-radius: 10px; background-color: #ffffff; }")
        left_card_layout = QVBoxLayout(left_card)
        left_card_layout.setContentsMargins(0, 0, 0, 0)
        left_card_layout.setSpacing(0)

        content_wrapper = QWidget()
        content_wrapper.setStyleSheet("background-color: #ffffff;")
        left_layout = QVBoxLayout(content_wrapper)
        left_layout.setContentsMargins(14, 14, 14, 14)
        left_layout.setSpacing(12)

        label_style = "font-size: 11px; font-weight: 600; color: #3a3a3a; background: transparent; border: none;"

        # ============ SEISMIC INPUTS BOX ============
        seismic_inputs_box = QFrame()
        seismic_inputs_box.setStyleSheet("""
            QFrame {
                border: 1px solid #9c9c9c;
                border-radius: 6px;
                background-color: #ffffff;
                padding: 0px;
            }
        """)
        seismic_inputs_box_layout = QVBoxLayout(seismic_inputs_box)
        seismic_title = QLabel("Seismic/Earthquake Load (EL) Inputs:")
        seismic_title.setStyleSheet("""
            font-size: 12px;
            font-weight: 700;
            color: #3a3a3a;
            background: transparent;
            border: none;
        """)
        seismic_inputs_box_layout.addWidget(seismic_title)

        seismic_inputs_box_layout.setContentsMargins(12, 12, 12, 12)
        seismic_inputs_box_layout.setSpacing(14)

        row = 0

        def add_combo(label_text, combo_items, attr_name, with_custom=False, placeholder="Custom Value", width_override=None):
            nonlocal row
            row_layout = QHBoxLayout()
            row_layout.setSpacing(10)
            
            lbl = QLabel(label_text)
            lbl.setStyleSheet(label_style)
            lbl.setMinimumWidth(LABEL_MIN_WIDTH)
            
            combo = QComboBox()
            combo.addItems(combo_items)
            combo.setFixedWidth(width_override if width_override else FIELD_WIDTH)
            combo.setFixedHeight(FIELD_HEIGHT)
            apply_field_style(combo)
            
            row_layout.addWidget(lbl)
            row_layout.addWidget(combo)
            
            custom = None
            if with_custom:
                custom = QLineEdit()
                custom.setPlaceholderText(placeholder)
                custom.setFixedSize(FIELD_WIDTH, FIELD_HEIGHT)
                custom.setEnabled(False)
                apply_field_style(custom)
                row_layout.addWidget(custom)
            
            row_layout.addStretch()
            seismic_inputs_box_layout.addLayout(row_layout)
            setattr(self, attr_name, combo)
            row += 1

            return combo, custom

        def add_line_edit(label_text, attr_name, default=None):
            nonlocal row
            row_layout = QHBoxLayout()
            row_layout.setSpacing(10)
            
            lbl = QLabel(label_text)
            lbl.setStyleSheet(label_style)
            lbl.setMinimumWidth(LABEL_MIN_WIDTH)
            
            line = QLineEdit()
            if default is not None:
                line.setText(default)
            line.setFixedSize(FIELD_WIDTH, FIELD_HEIGHT)
            apply_field_style(line)
            
            row_layout.addWidget(lbl)
            row_layout.addWidget(line)
            row_layout.addStretch()
            
            seismic_inputs_box_layout.addLayout(row_layout)
            setattr(self, attr_name, line)
            row += 1

        add_combo("Seismic Zone:", ["II", "III", "IV", "V"], "seismic_zone_combo")
        add_line_edit("Importance Factor:", "importance_factor_input", "1")
        add_combo("Type of Soil:", [
            "Type I – Rocky or Hard",
            "Type II – Medium Soil",
            "Type III – Soft Soil"
        ], "soil_type_combo")

        add_line_edit("Time Period:", "time_period_input")
        add_line_edit("Damping Percentage:", "damping_input", "2")
        add_combo("Response Reduction Factor:", ["1", "2", "3", "4", "5"], "response_factor_combo")

        if hasattr(self.owner, "project_seismic_zone"):
            self.seismic_zone_combo.setCurrentText(self.owner.project_seismic_zone)
        else:
            self.seismic_zone_combo.setCurrentText("II")  

        self.response_factor_combo.setCurrentText("1")
        _, self.dead_load_custom_input = add_combo(
            "Dead Load for Seismic Force (kN):",
            ["Automatic", "Custom"],
            "dead_load_seismic_combo",
            with_custom=True,
        )

        _, self.live_load_custom_input = add_combo(
            "Live Load for Seismic Force (kN):",
            ["Automatic", "Custom"],
            "live_load_seismic_combo",
            with_custom=True,
        )

        left_layout.addWidget(seismic_inputs_box)

        # ============ COMPUTED VALUES BOX ============
        computed_box = QFrame()
        computed_box.setStyleSheet("""
            QFrame {
                border: 1px solid #9c9c9c;
                border-radius: 6px;
                background-color: #ffffff;
                padding: 0px;
            }
        """)
        computed_box_layout = QVBoxLayout(computed_box)
        computed_box_layout.setContentsMargins(12, 12, 12, 12)
        computed_box_layout.setSpacing(14)

        # Add "Computed Values" title
        computed_title = QLabel("Computed Values")
        computed_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #3a3a3a; background: transparent; border: none;")
        computed_box_layout.addWidget(computed_title)

        computed_fields = [
            ("Zone Factor:", "zone_factor"),
            ("Spectral Acceleration Coefficient:", "spectral_coeff"),
            ("Horizontal Seismic Coefficient:", "horizontal_coeff"),
            ("Vertical Seismic Coefficient:", "vertical_coeff"),
        ]

        self.seismic_computed_fields = {}
        for label_text, field_name in computed_fields:
            row_layout = QHBoxLayout()
            row_layout.setSpacing(10)
            
            lbl = QLabel(label_text)
            lbl.setStyleSheet(label_style)
            lbl.setMinimumWidth(LABEL_MIN_WIDTH)
            
            field = QLineEdit()
            field.setFixedSize(FIELD_WIDTH, FIELD_HEIGHT)
            field.setReadOnly(True)
            field.setStyleSheet("""
                QLineEdit {
                    background-color: #f0f0f0;
                    border: 1px solid #8a8a8a;
                    border-radius: 5px;
                    padding: 5px 8px;
                    color: #5a5a5a;
                    font-size: 11px;
                }
            """)
            
            row_layout.addWidget(lbl)
            row_layout.addWidget(field)
            row_layout.addStretch()
            
            computed_box_layout.addLayout(row_layout)
            self.seismic_computed_fields[field_name] = field

        left_layout.addWidget(computed_box)
        left_layout.addStretch()
        left_card_layout.addWidget(content_wrapper)

        # ============ RIGHT CARD - Description Box ============
        right_card = owner._create_card()
        right_card.setStyleSheet("QFrame { border: 1px solid #9c9c9c; border-radius: 10px; background-color: #d4d4d4; }")
        right_card.setMinimumWidth(260)
        right_card.setMinimumHeight(420)
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(16, 16, 16, 16)
        right_layout.setSpacing(10)

        desc_title = QLabel("Description Box")
        desc_title.setAlignment(Qt.AlignCenter)
        desc_title.setStyleSheet("font-size: 12px; font-weight: 700; color: #000000; background: transparent; border: none;")
        right_layout.addWidget(desc_title)

        desc_text = QLabel(
            "Importance factor for normal, important, and critical bridges.\n\n"
            "Seismic zone factors are defined according to IRC 6 specifications.\n\n"
            "The spectral acceleration coefficient depends on soil type and time period."
        )
        desc_text.setWordWrap(True)
        desc_text.setStyleSheet("font-size: 11px; color: #4b4b4b; background: transparent; border: none;")
        right_layout.addWidget(desc_text)
        right_layout.addStretch()

        content_row.addWidget(left_card, 3)
        content_row.addWidget(right_card, 2)

        page_layout.addLayout(content_row)

        # Set scroll content and add to main layout
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

        # Connect signals
        self.dead_load_seismic_combo.currentTextChanged.connect(
            lambda _: self._toggle_seismic_custom_inputs()
        )
        self.live_load_seismic_combo.currentTextChanged.connect(
            lambda _: self._toggle_seismic_custom_inputs()
        )
        
        # Initialize state
        self._toggle_seismic_custom_inputs()
        self._apply_seismic_defaults()

    def _apply_seismic_defaults(self):
        self.seismic_zone_combo.setCurrentText(
            IRC_SEISMIC_DEFAULTS["seismic_zone"]
        )
        self.importance_factor_input.setText(
            IRC_SEISMIC_DEFAULTS["importance_factor"]
        )
        self.soil_type_combo.setCurrentText(
            IRC_SEISMIC_DEFAULTS["soil_type"]
        )
        self.damping_input.setText(
            IRC_SEISMIC_DEFAULTS["damping"]
        )
        self.response_factor_combo.setCurrentText(
            IRC_SEISMIC_DEFAULTS["response_reduction_factor"]
        )

        self.dead_load_seismic_combo.setCurrentText(
            IRC_SEISMIC_DEFAULTS["dead_load_mode"]
        )
        self.live_load_seismic_combo.setCurrentText(
            IRC_SEISMIC_DEFAULTS["live_load_mode"]
        )

        self.dead_load_custom_input.setDisabled(True)
        self.live_load_custom_input.setDisabled(True)


    def _toggle_seismic_custom_inputs(self):
        dead_is_custom = self.dead_load_seismic_combo.currentText() == "Custom"
        self.dead_load_custom_input.setEnabled(dead_is_custom)

        live_is_custom = self.live_load_seismic_combo.currentText() == "Custom"
        self.live_load_custom_input.setEnabled(live_is_custom)

    def reset_defaults(self):
        """Reset Seismic Load inputs to IRC default values"""
        self._apply_seismic_defaults()