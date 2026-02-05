from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QLineEdit,
    QFrame,

    QScrollArea,
)

from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style
from osdagbridge.core.bridge_types.plate_girder.ui_fields_additional_input import SEISMIC_LOAD_TAB_SCHEMA

    QGridLayout,
)

from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style



class SeismicLoadTab(QWidget):
    """Seismic/Earthquake Load tab content extracted from LoadingTab."""

    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner

        self.schema = SEISMIC_LOAD_TAB_SCHEMA

        self._build_ui()

    def _build_ui(self):
        owner = self.owner

        schema = self.schema

        LABEL_MIN_WIDTH = schema.get("label_width", 220)
        FIELD_WIDTH = schema.get("field_width", 180)
        FIELD_HEIGHT = schema.get("field_height", 28)

        self.setStyleSheet("background-color: #f5f5f5;")
     
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet("QScrollArea { background-color: #f5f5f5; border: none; }")

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: #f5f5f5;")
        page_layout = QVBoxLayout(scroll_content)


        self.setStyleSheet("background-color: #f5f5f5;")
        page_layout = QVBoxLayout(self)

        page_layout.setContentsMargins(12, 12, 12, 12)
        page_layout.setSpacing(12)

        content_row = QHBoxLayout()
        content_row.setContentsMargins(0, 0, 0, 0)
        content_row.setSpacing(16)

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

        for section in schema.get("sections", []):
            section_type = section.get("type")
            section_id = section.get("id")
         
            if section_type == "input_group" and section_id == "seismic_inputs_section":
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
                seismic_inputs_box_layout.setContentsMargins(12, 12, 12, 12)
                seismic_inputs_box_layout.setSpacing(14)

                seismic_title = QLabel(section.get("title", ""))
                seismic_title.setStyleSheet("font-size: 12px; font-weight: 700; color: #3a3a3a; background: transparent; border: none;")
                seismic_inputs_box_layout.addWidget(seismic_title)

                for field in section.get("fields", []):
                    field_type = field.get("type")
                    
                    row_layout = QHBoxLayout()
                    row_layout.setSpacing(10)
                    
                    lbl = QLabel(field.get("label", ""))
                    lbl.setStyleSheet(label_style)
                    lbl.setMinimumWidth(LABEL_MIN_WIDTH)
                    row_layout.addWidget(lbl)
    
                    if field_type == "combo":
                        widget = QComboBox()
                        widget.addItems(field.get("choices", []))
                        if field.get("default"):
                            widget.setCurrentText(field.get("default"))
                        widget.setFixedSize(FIELD_WIDTH, FIELD_HEIGHT)
                        apply_field_style(widget)
                        
                        bind_name = field.get("bind")
                        if bind_name:
                            setattr(self, bind_name, widget)
                        
                        row_layout.addWidget(widget)
                    
                    elif field_type == "line":
                        widget = QLineEdit()
                        if field.get("default"):
                            widget.setText(field.get("default"))
                        widget.setFixedSize(FIELD_WIDTH, FIELD_HEIGHT)
                        apply_field_style(widget)
                        
                        bind_name = field.get("bind")
                        if bind_name:
                            setattr(self, bind_name, widget)
                        
                        row_layout.addWidget(widget)
                    
                    elif field_type == "mode_line":
                        mode_combo = QComboBox()
                        mode_combo.addItems(field.get("mode_choices", []))
                        if field.get("default_mode"):
                            mode_combo.setCurrentText(field.get("default_mode"))
                        mode_combo.setFixedSize(FIELD_WIDTH, FIELD_HEIGHT)
                        apply_field_style(mode_combo)
                        
                        mode_bind = field.get("bind_mode")
                        if mode_bind:
                            setattr(self, mode_bind, mode_combo)
                        
                        row_layout.addWidget(mode_combo)
                        
                        value_input = QLineEdit()
                        value_input.setPlaceholderText(field.get("placeholder", ""))
                        value_input.setFixedSize(FIELD_WIDTH, FIELD_HEIGHT)
                        value_input.setEnabled(False)
                        apply_field_style(value_input)
                        
                        value_bind = field.get("bind_value")
                        if value_bind:
                            setattr(self, value_bind, value_input)
                        
                        row_layout.addWidget(value_input)
                    
                    row_layout.addStretch()
                    seismic_inputs_box_layout.addLayout(row_layout)

                left_layout.addWidget(seismic_inputs_box)
         
            elif section_type == "computed_group" and section_id == "computed_values_section":
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

                computed_title = QLabel(section.get("title", ""))
                computed_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #3a3a3a; background: transparent; border: none;")
                computed_box_layout.addWidget(computed_title)

                self.seismic_computed_fields = {}
                
                for field in section.get("fields", []):
                    row_layout = QHBoxLayout()
                    row_layout.setSpacing(10)
                    
                    lbl = QLabel(field.get("label", ""))
                    lbl.setStyleSheet(label_style)
                    lbl.setMinimumWidth(LABEL_MIN_WIDTH)
                    
                    computed_field = QLineEdit()
                    computed_field.setFixedSize(FIELD_WIDTH, FIELD_HEIGHT)
                    computed_field.setReadOnly(True)
                    computed_field.setStyleSheet("""
                        QLineEdit {
                            background-color: #f0f0f0;
                            border: 1px solid #8a8a8a;
                            border-radius: 5px;
                            padding: 5px 8px;
                            color: #5a5a5a;
                            font-size: 11px;
                        }
                    """)
                    
                    bind_name = field.get("bind")
                    if bind_name:
                        self.seismic_computed_fields[bind_name] = computed_field
                    
                    row_layout.addWidget(lbl)
                    row_layout.addWidget(computed_field)
                    row_layout.addStretch()
                    
                    computed_box_layout.addLayout(row_layout)

                left_layout.addWidget(computed_box)

        left_layout.addStretch()
        left_card_layout.addWidget(content_wrapper)

        right_card = owner._create_card()
        right_card.setStyleSheet("QFrame { border: 1px solid #9c9c9c; border-radius: 10px; background-color: #d4d4d4; }")
        right_card.setMinimumWidth(260)
        right_card.setMinimumHeight(420)

        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(16, 16, 16, 16)
        left_layout.setSpacing(12)

        title = QLabel("Seismic/Earthquake Load (EL) Inputs for Evaluation per IRC 6")
        title.setStyleSheet("font-size: 12px; font-weight: 700; color: #2b2b2b; background: transparent; border: none;")
        left_layout.addWidget(title)

        label_style = "font-size: 11px; color: #3a3a3a; background: transparent; border: none;"
        field_width = 120
        field_height = 28

        seismic_inputs_box = QFrame()
        seismic_inputs_box.setStyleSheet("QFrame { border: 1px solid #b2b2b2; border-radius: 8px; background-color: #ffffff; }")
        seismic_inputs_layout = QGridLayout(seismic_inputs_box)
        seismic_inputs_layout.setContentsMargins(12, 16, 12, 16)
        seismic_inputs_layout.setHorizontalSpacing(12)
        seismic_inputs_layout.setVerticalSpacing(6)
        seismic_inputs_layout.setColumnMinimumWidth(0, 200)
        seismic_inputs_layout.setColumnMinimumWidth(1, 140)
        seismic_inputs_layout.setColumnMinimumWidth(2, 140)
        seismic_inputs_layout.setColumnStretch(2, 1)

        row = 0

        def add_combo(label_text, combo_items, attr_name, with_custom=False, placeholder="Custom Value"):
            nonlocal row
            lbl = QLabel(label_text)
            lbl.setStyleSheet(label_style)
            lbl.setFixedHeight(field_height)
            combo = QComboBox()
            combo.addItems(combo_items)
            combo.setFixedSize(field_width, field_height)
            apply_field_style(combo)
            seismic_inputs_layout.addWidget(lbl, row, 0, Qt.AlignLeft | Qt.AlignVCenter)
            seismic_inputs_layout.addWidget(combo, row, 1, Qt.AlignLeft)
            setattr(owner, attr_name, combo)

            if with_custom:
                custom = QLineEdit()
                custom.setPlaceholderText(placeholder)
                custom.setFixedSize(field_width, field_height)
                custom.setEnabled(False)
                apply_field_style(custom)
                seismic_inputs_layout.addWidget(custom, row, 2, Qt.AlignLeft)
                row += 1
                return combo, custom

            row += 1

            return combo, None

        def add_line_edit(label_text, attr_name, default=None):
            nonlocal row
            lbl = QLabel(label_text)
            lbl.setStyleSheet(label_style)
            lbl.setFixedHeight(field_height)
            line = QLineEdit()
            if default is not None:
                line.setText(default)
            line.setFixedSize(field_width, field_height)
            apply_field_style(line)
            seismic_inputs_layout.addWidget(lbl, row, 0, Qt.AlignLeft | Qt.AlignVCenter)
            seismic_inputs_layout.addWidget(line, row, 1, Qt.AlignLeft)
            setattr(owner, attr_name, line)
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
        owner.response_factor_combo.setCurrentText("1")
        _, owner.dead_load_custom_input = add_combo(
            "Dead Load for Seismic Force (kN):",
            ["Automatic", "Custom"],
            "dead_load_seismic_combo",
            with_custom=True,
        )

        _, owner.live_load_custom_input = add_combo(
            "Live Load for Seismic Force (kN):",
            ["Automatic", "Custom"],
            "live_load_seismic_combo",
            with_custom=True,
        )

        left_layout.addWidget(seismic_inputs_box)

        computed_box = QFrame()
        computed_box.setStyleSheet("QFrame { border: 1px solid #b2b2b2; border-radius: 8px; background-color: #ffffff; }")
        computed_layout = QGridLayout(computed_box)
        computed_layout.setContentsMargins(12, 16, 12, 16)
        computed_layout.setHorizontalSpacing(12)
        computed_layout.setVerticalSpacing(6)
        computed_layout.setColumnMinimumWidth(0, 200)

        computed_fields = [
            ("Zone Factor:", "zone_factor"),
            ("Spectral Acceleration Coefficient:", "spectral_coeff"),
            ("Horizontal Seismic Coefficient:", "horizontal_coeff"),
            ("Vertical Seismic Coefficient:", "vertical_coeff"),
        ]

        owner.seismic_computed_fields = {}
        for idx, (label_text, field_name) in enumerate(computed_fields):
            lbl = QLabel(label_text)
            lbl.setStyleSheet(label_style)
            lbl.setFixedHeight(field_height)
            field = QLineEdit()
            field.setFixedSize(field_width, field_height)
            field.setReadOnly(True)
            apply_field_style(field)
            computed_layout.addWidget(lbl, idx, 0, Qt.AlignLeft | Qt.AlignVCenter)
            computed_layout.addWidget(field, idx, 1, Qt.AlignLeft)
            owner.seismic_computed_fields[field_name] = field

        left_layout.addWidget(computed_box)
        left_layout.addStretch()

        right_card = owner._create_card()
        right_card.setStyleSheet("QFrame { border: 1px solid #9c9c9c; border-radius: 10px; background-color: #d4d4d4; }")
        right_card.setMinimumWidth(200)
        right_card.setMinimumHeight(400)

        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(16, 16, 16, 16)
        right_layout.setSpacing(10)


        description = schema.get("description", {})
        desc_title = QLabel(description.get("title", ""))
        desc_title.setAlignment(Qt.AlignCenter)
        desc_title.setStyleSheet("font-size: 12px; font-weight: 700; color: #000000; background: transparent; border: none;")
        right_layout.addWidget(desc_title)

        desc_text = QLabel(description.get("text", ""))

        desc_title = QLabel("Description Box")
        desc_title.setAlignment(Qt.AlignCenter)
        desc_title.setStyleSheet("font-size: 12px; font-weight: 700; color: #2b2b2b; background: transparent; border: none;")
        right_layout.addWidget(desc_title)

        desc_text = QLabel("Importance factor for normal, important, and critical bridges.")

        desc_text.setWordWrap(True)
        desc_text.setStyleSheet("font-size: 11px; color: #4b4b4b; background: transparent; border: none;")
        right_layout.addWidget(desc_text)
        right_layout.addStretch()

        content_row.addWidget(left_card, 3)
        content_row.addWidget(right_card, 2)

        page_layout.addLayout(content_row)


        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

        seismic_inputs = next(
            (s for s in schema.get("sections", []) if s.get("id") == "seismic_inputs_section"),
            None
        )
        
        if seismic_inputs:
            for field in seismic_inputs.get("fields", []):
                on_mode_change = field.get("on_mode_change")
                if on_mode_change:
                    mode_bind = field.get("bind_mode")
                    if mode_bind and hasattr(self, mode_bind):
                        combo = getattr(self, mode_bind)
                        combo.currentTextChanged.connect(lambda _: self._toggle_seismic_custom_inputs())
      
        self._apply_seismic_defaults()
        self._toggle_seismic_custom_inputs()
    
        if hasattr(self.owner, "project_seismic_zone"):
            self.seismic_zone_combo.setCurrentText(self.owner.project_seismic_zone)

    def _apply_seismic_defaults(self):
        """Apply default values from schema"""
        seismic_inputs = next(
            (s for s in self.schema.get("sections", []) if s.get("id") == "seismic_inputs_section"),
            None
        )
        
        if not seismic_inputs:
            return
        
        for field in seismic_inputs.get("fields", []):
            bind_name = field.get("bind") or field.get("bind_mode")
            if not bind_name or not hasattr(self, bind_name):
                continue
            
            widget = getattr(self, bind_name)
            default_value = field.get("default") or field.get("default_mode")
            
            if default_value:
                if isinstance(widget, QComboBox):
                    widget.setCurrentText(default_value)
                elif isinstance(widget, QLineEdit):
                    widget.setText(default_value)

    def _toggle_seismic_custom_inputs(self):
        """Enable/disable custom inputs based on mode selection"""
        if hasattr(self, 'dead_load_seismic_combo') and hasattr(self, 'dead_load_custom_input'):
            dead_is_custom = self.dead_load_seismic_combo.currentText() == "Custom"
            self.dead_load_custom_input.setEnabled(dead_is_custom)

        if hasattr(self, 'live_load_seismic_combo') and hasattr(self, 'live_load_custom_input'):
            live_is_custom = self.live_load_seismic_combo.currentText() == "Custom"
            self.live_load_custom_input.setEnabled(live_is_custom)

    def reset_defaults(self):
        """Reset Seismic Load inputs to schema default values"""
        self._apply_seismic_defaults()
        self._toggle_seismic_custom_inputs()

        owner.dead_load_seismic_combo.currentTextChanged.connect(owner._on_dead_load_mode_changed)
        owner.live_load_seismic_combo.currentTextChanged.connect(owner._on_live_load_mode_changed)
